from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field


class SoftwareVersion(BaseModel):
    version: str = Field(description="Latest version released of the software.")


software_version_information = JsonOutputParser(pydantic_object=SoftwareVersion)
