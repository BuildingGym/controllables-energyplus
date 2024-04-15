import typing as _typing_

_KT, _VT = _typing_.TypeVar('_KT'), _typing_.TypeVar('_VT')

_typing_.Mapping[_KT, _VT]
_typing_.Iterable[tuple[_KT, _VT]]




def render(o: object):
    # TODO optional dep!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    import IPython as _ipython_
    import IPython.core.formatters

    import html as _html_

    formatted, _ = _ipython_.core.formatters.format_display_data(
        o, include=(
            'text/plain', 
            'text/html', 
        ),
    )
    return formatted.get('text/html', _html_.escape(formatted['text/plain']))


class MetaElement(type):
    pass

class Element(object, metaclass=MetaElement):
    def __init__(self, tag, attrs, child=None):
        self._tag = tag
        self._attrs = dict(attrs)
        self._child = child

    def _repr_html_(self):
        return rf'''<{self._tag} {
            str.join(' ', (
                rf'{key}="{value}"' 
                for key, value in self._attrs.items()
            ))
        }>{render(self._child) if self._child is not None else ''}</{self._tag}>'''
    
    # TODO
    @property
    def selector(self):
        raise NotImplementedError
    
class ClassElement(Element):
    def __init__(self, tag, attrs, child=None):
        super().__init__(
            tag=tag, 
            attrs={
                '__class__': type(self),
                '__id__': id(self),
                **dict(attrs),
            },
            child=child,
        )




class Details:
    def __init__(self, summary, content):
        self._summary = summary
        self._content = content

    # TODO __mime_repr__
    def _repr_html_(self):
        return rf'''<details>
            <summary>{render(self._summary)}</summary>
            {render(self._content)}
        </details>'''

class DescriptionList:
    def __init__(self, data: _typing_.Iterable[tuple[_KT, _VT]]):
        self._data = data

    def _repr_html_(self):
        return rf'''<dl>
            {str.join('', (
                rf'<dt>{render(key)}</dt><dd>{render(value)}</dd>' 
                for key, value in self._data
            ))}
        </dl>'''


import collections as _collections_

# TODO !!!!! recursive???
class DictView(_collections_.UserDict):
    def _repr_html_(self):
        return render(
            Details(
                summary=self.__class__.__name__, 
                content=DescriptionList(self.items()),
            )
        )