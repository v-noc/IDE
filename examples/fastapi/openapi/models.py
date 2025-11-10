from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Type, Union

from fastapi._compat import (
    PYDANTIC_V2,
    CoreSchema,
    GetJsonSchemaHandler,
    JsonSchemaValue,
    _model_rebuild,
    with_info_plain_validator_function,
)
from fastapi.logger import logger
from pydantic import AnyUrl, BaseModel, Field
from typing_extensions import Annotated, Literal, TypedDict
from typing_extensions import deprecated as typing_deprecated

try:
    import email_validator

    assert email_validator  # make autoflake ignore the unused import
    from pydantic import EmailStr
except ImportError:  # pragma: no cover

    class EmailStr(str):  # type: ignore
        """ID: 4b15dab2-e822-4fc3-888a-be00b490f6d7"""
        @classmethod
        def __get_validators__(cls) -> Iterable[Callable[..., Any]]:
            """ID: 87ed65f8-90ec-423a-ba24-290069851706"""
            yield cls.validate

        @classmethod
        def validate(cls, v: Any) -> str:
            """ID: 346b3260-60aa-42d2-9c98-8b09730d8dee"""
            logger.warning(
                "email-validator not installed, email fields will be treated as str.\n"
                "To install, run: pip install email-validator"
            )
            return str(v)

        @classmethod
        def _validate(cls, __input_value: Any, _: Any) -> str:
            """ID: 228c08a6-1af1-4500-96e1-b702692589c9"""
            logger.warning(
                "email-validator not installed, email fields will be treated as str.\n"
                "To install, run: pip install email-validator"
            )
            return str(__input_value)

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            """ID: df592682-59e3-4443-abcb-a0395e51ff8d"""
            return {"type": "string", "format": "email"}

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: Type[Any], handler: Callable[[Any], CoreSchema]
        ) -> CoreSchema:
            """ID: 395c7b2d-19ea-4778-8b27-316320bab09a"""
            return with_info_plain_validator_function(cls._validate)


class BaseModelWithConfig(BaseModel):
    """ID: 607027dc-c1d4-4b3d-b884-d4c36eb9d76e"""
    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            """ID: d873901b-7b4d-4d1f-b1be-1111921bbb06"""
            extra = "allow"


class Contact(BaseModelWithConfig):
    """ID: c1fdd01d-2bb4-4f52-bfea-9cfdd4b6d64a"""
    name: Optional[str] = None
    url: Optional[AnyUrl] = None
    email: Optional[EmailStr] = None


class License(BaseModelWithConfig):
    """ID: 818df19a-54f6-4c8d-a69b-d1140aba3f2f"""
    name: str
    identifier: Optional[str] = None
    url: Optional[AnyUrl] = None


class Info(BaseModelWithConfig):
    """ID: ba25b65e-21c3-4792-8a62-00bfd9954bae"""
    title: str
    summary: Optional[str] = None
    description: Optional[str] = None
    termsOfService: Optional[str] = None
    contact: Optional[Contact] = None
    license: Optional[License] = None
    version: str


class ServerVariable(BaseModelWithConfig):
    """ID: 1f732bcb-4bf7-41f6-9d1c-e2c6048fb5a3"""
    enum: Annotated[Optional[List[str]], Field(min_length=1)] = None
    default: str
    description: Optional[str] = None


class Server(BaseModelWithConfig):
    """ID: be36c52f-7457-4c18-9964-8dc1396b64fe"""
    url: Union[AnyUrl, str]
    description: Optional[str] = None
    variables: Optional[Dict[str, ServerVariable]] = None


class Reference(BaseModel):
    """ID: 1ebcb742-8601-4a58-8f00-ad19d4b8445c"""
    ref: str = Field(alias="$ref")


class Discriminator(BaseModel):
    """ID: cdcd57a0-32a2-4b40-97dd-4fc409924e2f"""
    propertyName: str
    mapping: Optional[Dict[str, str]] = None


class XML(BaseModelWithConfig):
    """ID: 3d7b7a20-073b-4024-9008-cb8f071e7cf3"""
    name: Optional[str] = None
    namespace: Optional[str] = None
    prefix: Optional[str] = None
    attribute: Optional[bool] = None
    wrapped: Optional[bool] = None


class ExternalDocumentation(BaseModelWithConfig):
    """ID: 3b5cc410-ba9c-49f8-bdf7-f9f9810ec9ed"""
    description: Optional[str] = None
    url: AnyUrl


# Ref JSON Schema 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation#name-type
SchemaType = Literal[
    "array", "boolean", "integer", "null", "number", "object", "string"
]


class Schema(BaseModelWithConfig):
    """ID: 61940cbf-1e9c-4ecf-bed1-600d187818e0"""
    # Ref: JSON Schema 2020-12: https://json-schema.org/draft/2020-12/json-schema-core.html#name-the-json-schema-core-vocabu
    # Core Vocabulary
    schema_: Optional[str] = Field(default=None, alias="$schema")
    vocabulary: Optional[str] = Field(default=None, alias="$vocabulary")
    id: Optional[str] = Field(default=None, alias="$id")
    anchor: Optional[str] = Field(default=None, alias="$anchor")
    dynamicAnchor: Optional[str] = Field(default=None, alias="$dynamicAnchor")
    ref: Optional[str] = Field(default=None, alias="$ref")
    dynamicRef: Optional[str] = Field(default=None, alias="$dynamicRef")
    defs: Optional[Dict[str, "SchemaOrBool"]] = Field(default=None, alias="$defs")
    comment: Optional[str] = Field(default=None, alias="$comment")
    # Ref: JSON Schema 2020-12: https://json-schema.org/draft/2020-12/json-schema-core.html#name-a-vocabulary-for-applying-s
    # A Vocabulary for Applying Subschemas
    allOf: Optional[List["SchemaOrBool"]] = None
    anyOf: Optional[List["SchemaOrBool"]] = None
    oneOf: Optional[List["SchemaOrBool"]] = None
    not_: Optional["SchemaOrBool"] = Field(default=None, alias="not")
    if_: Optional["SchemaOrBool"] = Field(default=None, alias="if")
    then: Optional["SchemaOrBool"] = None
    else_: Optional["SchemaOrBool"] = Field(default=None, alias="else")
    dependentSchemas: Optional[Dict[str, "SchemaOrBool"]] = None
    prefixItems: Optional[List["SchemaOrBool"]] = None
    # TODO: uncomment and remove below when deprecating Pydantic v1
    # It generates a list of schemas for tuples, before prefixItems was available
    # items: Optional["SchemaOrBool"] = None
    items: Optional[Union["SchemaOrBool", List["SchemaOrBool"]]] = None
    contains: Optional["SchemaOrBool"] = None
    properties: Optional[Dict[str, "SchemaOrBool"]] = None
    patternProperties: Optional[Dict[str, "SchemaOrBool"]] = None
    additionalProperties: Optional["SchemaOrBool"] = None
    propertyNames: Optional["SchemaOrBool"] = None
    unevaluatedItems: Optional["SchemaOrBool"] = None
    unevaluatedProperties: Optional["SchemaOrBool"] = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-structural
    # A Vocabulary for Structural Validation
    type: Optional[Union[SchemaType, List[SchemaType]]] = None
    enum: Optional[List[Any]] = None
    const: Optional[Any] = None
    multipleOf: Optional[float] = Field(default=None, gt=0)
    maximum: Optional[float] = None
    exclusiveMaximum: Optional[float] = None
    minimum: Optional[float] = None
    exclusiveMinimum: Optional[float] = None
    maxLength: Optional[int] = Field(default=None, ge=0)
    minLength: Optional[int] = Field(default=None, ge=0)
    pattern: Optional[str] = None
    maxItems: Optional[int] = Field(default=None, ge=0)
    minItems: Optional[int] = Field(default=None, ge=0)
    uniqueItems: Optional[bool] = None
    maxContains: Optional[int] = Field(default=None, ge=0)
    minContains: Optional[int] = Field(default=None, ge=0)
    maxProperties: Optional[int] = Field(default=None, ge=0)
    minProperties: Optional[int] = Field(default=None, ge=0)
    required: Optional[List[str]] = None
    dependentRequired: Optional[Dict[str, Set[str]]] = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-vocabularies-for-semantic-c
    # Vocabularies for Semantic Content With "format"
    format: Optional[str] = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-the-conten
    # A Vocabulary for the Contents of String-Encoded Data
    contentEncoding: Optional[str] = None
    contentMediaType: Optional[str] = None
    contentSchema: Optional["SchemaOrBool"] = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-basic-meta
    # A Vocabulary for Basic Meta-Data Annotations
    title: Optional[str] = None
    description: Optional[str] = None
    default: Optional[Any] = None
    deprecated: Optional[bool] = None
    readOnly: Optional[bool] = None
    writeOnly: Optional[bool] = None
    examples: Optional[List[Any]] = None
    # Ref: OpenAPI 3.1.0: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#schema-object
    # Schema Object
    discriminator: Optional[Discriminator] = None
    xml: Optional[XML] = None
    externalDocs: Optional[ExternalDocumentation] = None
    example: Annotated[
        Optional[Any],
        typing_deprecated(
            "Deprecated in OpenAPI 3.1.0 that now uses JSON Schema 2020-12, "
            "although still supported. Use examples instead."
        ),
    ] = None


# Ref: https://json-schema.org/draft/2020-12/json-schema-core.html#name-json-schema-documents
# A JSON Schema MUST be an object or a boolean.
SchemaOrBool = Union[Schema, bool]


class Example(TypedDict, total=False):
    """ID: 05e73da7-1a3e-4258-bbc4-a9803a0b7f00"""
    summary: Optional[str]
    description: Optional[str]
    value: Optional[Any]
    externalValue: Optional[AnyUrl]

    if PYDANTIC_V2:  # type: ignore [misc]
        __pydantic_config__ = {"extra": "allow"}

    else:

        class Config:
            """ID: c3319bb5-252a-47ed-a76e-f64bea8f0b70"""
            extra = "allow"


class ParameterInType(Enum):
    """ID: 6c1c7274-0a83-45fc-9834-d29bbefa444b"""
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


class Encoding(BaseModelWithConfig):
    """ID: 59261797-0cab-4203-9c2a-6858ccfe4492"""
    contentType: Optional[str] = None
    headers: Optional[Dict[str, Union["Header", Reference]]] = None
    style: Optional[str] = None
    explode: Optional[bool] = None
    allowReserved: Optional[bool] = None


class MediaType(BaseModelWithConfig):
    """ID: 82271f68-be2d-45c2-bcec-dd1979752b66"""
    schema_: Optional[Union[Schema, Reference]] = Field(default=None, alias="schema")
    example: Optional[Any] = None
    examples: Optional[Dict[str, Union[Example, Reference]]] = None
    encoding: Optional[Dict[str, Encoding]] = None


class ParameterBase(BaseModelWithConfig):
    """ID: 208fe18c-707b-4f97-b0a6-98d5b4ce603f"""
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: Optional[bool] = None
    # Serialization rules for simple scenarios
    style: Optional[str] = None
    explode: Optional[bool] = None
    allowReserved: Optional[bool] = None
    schema_: Optional[Union[Schema, Reference]] = Field(default=None, alias="schema")
    example: Optional[Any] = None
    examples: Optional[Dict[str, Union[Example, Reference]]] = None
    # Serialization rules for more complex scenarios
    content: Optional[Dict[str, MediaType]] = None


class Parameter(ParameterBase):
    """ID: 64876c4f-0f6e-46c3-9c3d-c0f666c7761b"""
    name: str
    in_: ParameterInType = Field(alias="in")


class Header(ParameterBase):
    """ID: 8033e9c1-db4c-4079-901c-c9da63134b5d"""
    pass


class RequestBody(BaseModelWithConfig):
    """ID: eebbdcd5-a3b5-4def-a267-45c11ddb2fb1"""
    description: Optional[str] = None
    content: Dict[str, MediaType]
    required: Optional[bool] = None


class Link(BaseModelWithConfig):
    """ID: 48775aef-bbbb-4098-ac9d-950bec1796f7"""
    operationRef: Optional[str] = None
    operationId: Optional[str] = None
    parameters: Optional[Dict[str, Union[Any, str]]] = None
    requestBody: Optional[Union[Any, str]] = None
    description: Optional[str] = None
    server: Optional[Server] = None


class Response(BaseModelWithConfig):
    """ID: 9109d7ad-273e-485a-8c05-63ca1a5997d6"""
    description: str
    headers: Optional[Dict[str, Union[Header, Reference]]] = None
    content: Optional[Dict[str, MediaType]] = None
    links: Optional[Dict[str, Union[Link, Reference]]] = None


class Operation(BaseModelWithConfig):
    """ID: 36349f43-62d3-403f-bb33-447695a878c2"""
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentation] = None
    operationId: Optional[str] = None
    parameters: Optional[List[Union[Parameter, Reference]]] = None
    requestBody: Optional[Union[RequestBody, Reference]] = None
    # Using Any for Specification Extensions
    responses: Optional[Dict[str, Union[Response, Any]]] = None
    callbacks: Optional[Dict[str, Union[Dict[str, "PathItem"], Reference]]] = None
    deprecated: Optional[bool] = None
    security: Optional[List[Dict[str, List[str]]]] = None
    servers: Optional[List[Server]] = None


class PathItem(BaseModelWithConfig):
    """ID: 4f8a7501-4936-4b16-91ba-1934ffcbe848"""
    ref: Optional[str] = Field(default=None, alias="$ref")
    summary: Optional[str] = None
    description: Optional[str] = None
    get: Optional[Operation] = None
    put: Optional[Operation] = None
    post: Optional[Operation] = None
    delete: Optional[Operation] = None
    options: Optional[Operation] = None
    head: Optional[Operation] = None
    patch: Optional[Operation] = None
    trace: Optional[Operation] = None
    servers: Optional[List[Server]] = None
    parameters: Optional[List[Union[Parameter, Reference]]] = None


class SecuritySchemeType(Enum):
    """ID: 22d5a8fd-4b47-476c-bd1d-00417b246dd4"""
    apiKey = "apiKey"
    http = "http"
    oauth2 = "oauth2"
    openIdConnect = "openIdConnect"


class SecurityBase(BaseModelWithConfig):
    """ID: ad2ecfe3-d52b-4166-8e0f-40c921132997"""
    type_: SecuritySchemeType = Field(alias="type")
    description: Optional[str] = None


class APIKeyIn(Enum):
    """ID: cade9ecc-1afe-44ac-8dbc-464467ee137b"""
    query = "query"
    header = "header"
    cookie = "cookie"


class APIKey(SecurityBase):
    """ID: d1719e3a-57f3-4d25-bcbd-e8ff2319fa57"""
    type_: SecuritySchemeType = Field(default=SecuritySchemeType.apiKey, alias="type")
    in_: APIKeyIn = Field(alias="in")
    name: str


class HTTPBase(SecurityBase):
    """ID: 57d2008f-5484-4d5c-b4f3-c38b9763eb14"""
    type_: SecuritySchemeType = Field(default=SecuritySchemeType.http, alias="type")
    scheme: str


class HTTPBearer(HTTPBase):
    """ID: af8c5120-d6a3-43db-931b-7ccef82d51be"""
    scheme: Literal["bearer"] = "bearer"
    bearerFormat: Optional[str] = None


class OAuthFlow(BaseModelWithConfig):
    """ID: ee2a962d-af85-4338-adbf-392d049eac1a"""
    refreshUrl: Optional[str] = None
    scopes: Dict[str, str] = {}


class OAuthFlowImplicit(OAuthFlow):
    """ID: 17faf118-b55c-4adb-9861-7e353984a61d"""
    authorizationUrl: str


class OAuthFlowPassword(OAuthFlow):
    """ID: b5671178-74ee-4b07-aca2-367e1566db25"""
    tokenUrl: str


class OAuthFlowClientCredentials(OAuthFlow):
    """ID: 44f3bebf-ffc0-4ede-b33c-3e10d3eec7ff"""
    tokenUrl: str


class OAuthFlowAuthorizationCode(OAuthFlow):
    """ID: 2e873ddc-b95d-41d3-93f6-1b4cd9a1a56b"""
    authorizationUrl: str
    tokenUrl: str


class OAuthFlows(BaseModelWithConfig):
    """ID: 91defa2e-8266-477e-b967-6b95c29178f1"""
    implicit: Optional[OAuthFlowImplicit] = None
    password: Optional[OAuthFlowPassword] = None
    clientCredentials: Optional[OAuthFlowClientCredentials] = None
    authorizationCode: Optional[OAuthFlowAuthorizationCode] = None


class OAuth2(SecurityBase):
    """ID: 8ede7289-c7f3-40fe-85d1-c6d7a599b525"""
    type_: SecuritySchemeType = Field(default=SecuritySchemeType.oauth2, alias="type")
    flows: OAuthFlows


class OpenIdConnect(SecurityBase):
    """ID: d21dafef-0866-4a0b-a95e-2b9b28ad5f23"""
    type_: SecuritySchemeType = Field(
        default=SecuritySchemeType.openIdConnect, alias="type"
    )
    openIdConnectUrl: str


SecurityScheme = Union[APIKey, HTTPBase, OAuth2, OpenIdConnect, HTTPBearer]


class Components(BaseModelWithConfig):
    """ID: 948b10eb-b9cf-437d-b133-1a25c136ff7e"""
    schemas: Optional[Dict[str, Union[Schema, Reference]]] = None
    responses: Optional[Dict[str, Union[Response, Reference]]] = None
    parameters: Optional[Dict[str, Union[Parameter, Reference]]] = None
    examples: Optional[Dict[str, Union[Example, Reference]]] = None
    requestBodies: Optional[Dict[str, Union[RequestBody, Reference]]] = None
    headers: Optional[Dict[str, Union[Header, Reference]]] = None
    securitySchemes: Optional[Dict[str, Union[SecurityScheme, Reference]]] = None
    links: Optional[Dict[str, Union[Link, Reference]]] = None
    # Using Any for Specification Extensions
    callbacks: Optional[Dict[str, Union[Dict[str, PathItem], Reference, Any]]] = None
    pathItems: Optional[Dict[str, Union[PathItem, Reference]]] = None


class Tag(BaseModelWithConfig):
    """ID: 7368b8b2-034b-49d9-924a-f0ec08c1e97d"""
    name: str
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentation] = None


class OpenAPI(BaseModelWithConfig):
    """ID: ede8d05e-cc45-4991-b22a-d0d3e8b16213"""
    openapi: str
    info: Info
    jsonSchemaDialect: Optional[str] = None
    servers: Optional[List[Server]] = None
    # Using Any for Specification Extensions
    paths: Optional[Dict[str, Union[PathItem, Any]]] = None
    webhooks: Optional[Dict[str, Union[PathItem, Reference]]] = None
    components: Optional[Components] = None
    security: Optional[List[Dict[str, List[str]]]] = None
    tags: Optional[List[Tag]] = None
    externalDocs: Optional[ExternalDocumentation] = None


_model_rebuild(Schema)
_model_rebuild(Operation)
_model_rebuild(Encoding)
