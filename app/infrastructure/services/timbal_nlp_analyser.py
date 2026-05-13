"""Implementació Timbal del port NlpAnalyserPort (RF-05, RN-12)."""
import asyncio
import json
import logging

import fitz  # pymupdf
from timbal import Agent
from timbal.types.file import File

from app.application.ports.nlp_analyser_port import NlpAnalyserPort
from app.domain.entities.document_analysis import DocumentAnalysis

logger = logging.getLogger(__name__)

# Providers que suporten arxius PDF natius — la resta necessiten extracció de text
_PDF_CAPABLE_PROVIDERS = {"google", "anthropic"}

# Groq free tier: ~12.000 tokens/request. Reservem ~2.000 per system_prompt + resposta.
# 1 token ≈ 4 chars → 10.000 tokens ≈ 40.000 chars. Usem 32.000 per marge.
_MAX_TEXT_CHARS = 32_000

_SYSTEM_PROMPT = """Ets un expert en licitacions públiques catalanes.
Analitza els documents PDF adjunts d'una licitació i retorna un JSON amb exactament aquests 7 camps:

{
  "solvencia": <0-30>,
  "criteris_adjudicacio": <0-25>,
  "clausules_atipiques": <0-20>,
  "procediment": <0-15>,
  "condicions_execucio": <0-10>,
  "comentaris_per_doc": {
    "<nom_fitxer_1.pdf>": "<comentari breu sobre aquest document en català>",
    "<nom_fitxer_2.pdf>": "<comentari breu sobre aquest document en català>"
  },
  "recomendacio": "<raonament GO o NO GO en 2-4 frases en català>"
}

Criteris de puntuació (RN-12):
- solvencia (0-30): Requisits de solvència tècnica i econòmica assolibles per una empresa mitjana.
  30 = requisits molt accessibles, 0 = requisits prohibitius.
- criteris_adjudicacio (0-25): Criteris d'adjudicació favorables (preu, experiència, termini).
  25 = molt favorables, 0 = molt desfavorables.
- clausules_atipiques (0-20): Absència de clàusules atípiques o restrictives.
  20 = cap clàusula problemàtica, 0 = moltes clàusules restrictives.
- procediment (0-15): Tipus de procediment d'accés (obert > restringit > negociat).
  15 = procediment obert, 0 = procediment molt restringit.
- condicions_execucio (0-10): Condicions d'execució raonables (terminis, penalitats, garanties).
  10 = condicions molt raonables, 0 = condicions molt exigents.

Per a comentaris_per_doc: usa els noms de fitxer exactes que t'indiquen i escriu 1-2 frases
en català explicant els aspectes clau d'aquell document per a la decisió GO/REVISAR/NO GO.

Per a recomendacio: escriu "GO — <raonament>", "REVISAR — <raonament>" o "NO GO — <raonament>" en 2-4 frases en català,
resumint per què la licitació és o no és viable per a l'empresa.
Usa REVISAR quan hi ha aspectes positius però també dubtes significatius que requereixen anàlisi addicional.

Respon ÚNICAMENT amb el JSON dels 7 camps, sense cap altre text."""


class TimbalNlpAnalyser(NlpAnalyserPort):
    """Analitzador NLP config-driven basat en l'agent Timbal (RF-05).

    El model i la clau API es configuren via settings (llm_model / llm_api_key).
    Providers amb suport natiu de PDF (google, anthropic): envien File objects.
    Resta de providers (groq, openai, mistral...): extreuen text amb pymupdf.

    No té tests automàtics perquè és un servei extern amb model de llenguatge.
    Es valida manualment en entorn de desenvolupament.
    """

    def __init__(self, model: str, api_key: str) -> None:
        """Inicialitza l'analitzador amb el model i la clau API configurats.

        Args:
            model:   Identificador del model en format 'provider/nom' (p.e. 'groq/llama-3.3-70b-versatile').
            api_key: Clau d'autenticació per al provider del model.
        """
        self._model = model
        provider = model.split("/")[0]
        key_hint = f"...{api_key[-4:]}" if len(api_key) > 4 else "(empty)"
        mode = "PDF natiu" if provider in _PDF_CAPABLE_PROVIDERS else "text extret (pymupdf)"
        logger.info(
            "[NLP] Model: %s | Provider: %s | API Key: %s | Mode: %s",
            model, provider, key_hint, mode,
        )
        self._agent = Agent(
            name="TimbalNlpAnalyser",
            model=model,
            api_key=api_key,
            system_prompt=_SYSTEM_PROMPT,
        )

    def analyse(
        self,
        expedient_id: str,
        documents: list[bytes],
        filenames: list[str] | None = None,
    ) -> DocumentAnalysis:
        """Analitza els documents PDF d'una licitació i retorna la puntuació (RN-12).

        Envia els PDFs com a File objects a l'agent Timbal.
        Parseja la resposta JSON i construeix un DocumentAnalysis validat.
        Si no hi ha documents, retorna una anàlisi amb tots els criteris a 0.

        Args:
            expedient_id: Identificador únic de l'expedient analitzat.
            documents:    Llista de continguts binaris dels PDFs obligatoris.
            filenames:    Noms dels fitxers (en el mateix ordre que documents),
                          usats pel LLM per generar comentaris_per_doc.

        Returns:
            DocumentAnalysis amb les puntuacions, comentaris per document i recomanació.
        """
        if not documents:
            return DocumentAnalysis(
                expedient_id=expedient_id,
                solvencia=0,
                criteris_adjudicacio=0,
                clausules_atipiques=0,
                procediment=0,
                condicions_execucio=0,
            )

        provider = self._model.split("/")[0]
        names = filenames or [
            f"document_{i+1}.pdf" for i in range(len(documents))]
        if provider in _PDF_CAPABLE_PROVIDERS:
            prompt: str | list = [
                f"Analitza els documents de la licitació {expedient_id}. "
                f"Noms dels fitxers: {', '.join(names)}.",
                *[File.validate(pdf_bytes) for pdf_bytes in documents],
            ]
        else:
            extracted = self._extract_text_from_pdfs(documents)
            if len(extracted) > _MAX_TEXT_CHARS:
                logger.warning(
                    "[NLP] Text truncat de %d a %d chars per %s",
                    len(extracted), _MAX_TEXT_CHARS, expedient_id,
                )
                extracted = extracted[:_MAX_TEXT_CHARS]
            filenames_hint = f"Noms dels fitxers: {', '.join(names)}.\n\n"
            prompt = (
                f"Analitza els documents de la licitació {expedient_id}.\n\n"
                f"{filenames_hint}{extracted}"
                if extracted
                else f"Analitza la licitació {expedient_id}. No hi ha text disponible."
            )
        try:
            result = asyncio.run(self._agent(prompt=prompt).collect())
            raw_text = result.output.collect_text() if result.output else ""
        except Exception as exc:  # noqa: BLE001
            logger.error("[NLP] Error del model %s per %s: %s",
                         self._model, expedient_id, str(exc)[:300])
            return DocumentAnalysis(
                expedient_id=expedient_id,
                solvencia=0,
                criteris_adjudicacio=0,
                clausules_atipiques=0,
                procediment=0,
                condicions_execucio=0,
            )

        scores = self._parse_response(raw_text)
        return DocumentAnalysis(
            expedient_id=expedient_id,
            solvencia=scores["solvencia"],
            criteris_adjudicacio=scores["criteris_adjudicacio"],
            clausules_atipiques=scores["clausules_atipiques"],
            procediment=scores["procediment"],
            condicions_execucio=scores["condicions_execucio"],
            comentaris_per_doc=scores["comentaris_per_doc"],
            recomendacio=scores["recomendacio"],
        )

    @staticmethod
    def _extract_text_from_pdfs(documents: list[bytes]) -> str:
        """Extreu el text de cada PDF i el concatena en un sol string.

        Usa pymupdf per obrir cada document en memòria. Si un PDF és invàlid
        o no conté text, s'ignora sense aturar el processament.

        Args:
            documents: Llista de continguts binaris dels PDFs.

        Returns:
            Text concatenat de tots els documents, separat per doble salt de línia.
        """
        parts: list[str] = []
        for pdf_bytes in documents:
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                text = "\n".join(page.get_text("text") for page in doc)
                if text.strip():
                    parts.append(text.strip())
            except Exception:  # noqa: BLE001
                pass
        return "\n\n".join(parts)

    @staticmethod
    def _parse_response(raw: str) -> dict:
        """Parseja la resposta JSON de l'agent i retorna el diccionari de puntuacions.

        Si el parseo falla (resposta malformada), retorna tots els criteris a 0
        per evitar que el pipeline s'aturi per un error de format.

        Args:
            raw: Text de resposta de l'agent (ha de ser JSON pur).

        Returns:
            Diccionari amb les 5 claus de puntuació com a enters.
        """
        _zero = {
            "solvencia": 0,
            "criteris_adjudicacio": 0,
            "clausules_atipiques": 0,
            "procediment": 0,
            "condicions_execucio": 0,
            "comentaris_per_doc": {},
            "recomendacio": "",
        }
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start == -1 or end == 0:
                return _zero
            data = json.loads(raw[start:end])
            return {
                "solvencia": int(data.get("solvencia", 0)),
                "criteris_adjudicacio": int(data.get("criteris_adjudicacio", 0)),
                "clausules_atipiques": int(data.get("clausules_atipiques", 0)),
                "procediment": int(data.get("procediment", 0)),
                "condicions_execucio": int(data.get("condicions_execucio", 0)),
                "comentaris_per_doc": data.get("comentaris_per_doc", {}) or {},
                "recomendacio": str(data.get("recomendacio", "")),
            }
        except (json.JSONDecodeError, ValueError):
            return _zero
