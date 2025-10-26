class DocumentProcessingError(Exception):
    """Exceção base para erros de processamento de documentos."""

    pass


class DocumentReadError(DocumentProcessingError):
    """Exceção para erros de leitura de documentos."""

    pass


class DocumentWriteError(DocumentProcessingError):
    """Exceção para erros de escrita de documentos."""

    pass
