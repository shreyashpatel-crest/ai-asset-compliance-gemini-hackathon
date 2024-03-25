from langchain.serpapi import SerpAPIWrapper


def get_software_information(text: str) -> str:
    """Searches for software home page.
    Args:
        text (str): search text

    Returns:
        str: Software url.
    """
    search = SerpAPIWrapper()
    result = search.run(f"{text}")
    return result
