"""Descarga de licitaciones públicas usando w2flow."""
import httpx

URL_LICITATIONS = "https://contractaciopublica.cat/portal-api/"

#  ?page=0&inclourePublicacionsPlacsp=false&tipusExpedient=1&ambit=1500001&ambitGeografic=1&procedimentAdjudicacio=401&sortField=dataUltimaPublicacio&sortOrder=desc


def download_documents():
    """Descarga la documentación de las licitaciones públicas."""
    with httpx.Client(base_url=URL_LICITATIONS, timeout=30) as client:
        response = client.get("cerca-avancada", params={
            "page": 0,
            "inclourePublicacionsPlacsp": "false",
            "tipusExpedient": 1,
            "ambit": 1500001,
            "ambitGeografic": 1,
            "procedimentAdjudicacio": 401,
            "sortField": "dataUltimaPublicacio",
            "sortOrder": "desc",
        })
        response.raise_for_status()
        licitations = response.json()
        print(f"Descargadas {len(licitations)} licitaciones.")
        print("Mostramos las licitaciones:")
        for licitation in licitations:
            if licitation:
                print(licitation)
            else:
                print("No se encontraron licitaciones.")


def main():
    """Función principal para ejecutar el proceso de descarga."""
    print("Iniciando descarga de licitaciones públicas...")
    download_documents()
    print("Proceso completado.")


if __name__ == "__main__":
    main()
