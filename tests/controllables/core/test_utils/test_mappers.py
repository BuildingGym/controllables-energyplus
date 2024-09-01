from controllables.core.utils import mappers as _target_

class Test_CollectionMapper:
    # TODO more cases

    def test_same_struct(self):
        assert (
            _target_.CollectionMapper(
                next_mapper=(lambda f0, f1: (f0, f1)),
            )
        )(
            dict(
                a=1, 
                b=dict(a=1), 
                c=tuple((1,)), 
                d=tuple([dict(a=1), dict(a=2)])
            ), 
            dict(
                a=10, 
                b=dict(a=10), 
                c=tuple((10,)), 
                d=tuple([dict(a=10), dict(a=20)])
            ),
        ) == dict(
            a=(1, 10), 
            b=dict(a=(1, 10)), 
            c=tuple(((1, 10),)), 
            d=tuple([dict(a=(1, 10)), dict(a=(2, 20))])
        )

    def test_diff_struct(self):
        assert (
            _target_.CollectionMapper(
                next_mapper=(lambda f0, f1: (f0, f1)),
            )
        )(
            dict(
                a=1, 
                b=dict(a=1), 
                c=tuple((1,)), 
                d=tuple([dict(a=1), dict(a=2)])
            ), 
            dict(
                a=10, 
                #b=dict(a=10), 
                c=tuple((10,)), 
                d=tuple([dict(a=10), dict(a=20)])
            ),
        ) == dict(
            a=(1, 10), 
            c=tuple(((1, 10),)), 
            d=tuple([dict(a=(1, 10)), dict(a=(2, 20))])
        )
