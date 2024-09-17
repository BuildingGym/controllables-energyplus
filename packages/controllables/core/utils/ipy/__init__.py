from . import (
    html,
)

__all__ = [
    'html',
]


from ...errors import OptionalModuleNotFoundError

def repr_html(obj: object):
    r"""
    TODO

    .. doctest::
            
        >>> from IPython.display import HTML
        >>> repr_html(HTML('yep'))
        'yep'
        >>> repr_html('yep')
        '&#x27;yep&#x27;'

    """

    try:
        from IPython.core.formatters import format_display_data
    except ModuleNotFoundError as e:
        raise OptionalModuleNotFoundError.suggest(['ipython']) from e

    import html as _html_

    formatted, _ = format_display_data(
        obj, include=(
            'text/plain', 
            'text/html', 
        ),
    )
    return formatted.get(
        'text/html', 
        _html_.escape(formatted['text/plain']),
    )


# TODO
__all__ = [
    'repr_html',
]