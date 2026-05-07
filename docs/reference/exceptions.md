# Excepciones

Jerarquía completa de excepciones del SDK. Toda excepción del cliente hereda de `DatosMexicoError`.

```
DatosMexicoError
├── ConfigurationError      (parámetros inválidos al crear el cliente)
├── NetworkError            (problemas de red genéricos)
│   └── TimeoutError        (timeout HTTP)
├── ApiError                (HTTP 4xx / 5xx clasificados)
│   ├── BadRequestError     (HTTP 400)
│   ├── AuthenticationError (HTTP 401)
│   ├── AuthorizationError  (HTTP 403)
│   ├── NotFoundError       (HTTP 404)
│   ├── RateLimitError      (HTTP 429)
│   └── ServerError         (HTTP 5xx)
└── ValidationError         (Pydantic validation o helper-side validation)
```

→ Para guía de uso, ver [Quickstart §5](../quickstart.md#5-manejo-basico-de-errores).

## Clases

::: datos_mexico.exceptions
    options:
      heading_level: 3
      show_root_heading: false
      show_root_toc_entry: false
