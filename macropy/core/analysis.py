from walkers import *
from macropy.core import merge_dicts

@Walker
def find_names(tree, collect, stop, **kw):
    if type(tree) in [Attribute, Subscript]:
        stop()
    if isinstance(tree, Name):
        collect((tree.id, tree))

@Walker
def find_assignments(tree, collect, stop, **kw):
    if type(tree) in [ClassDef, FunctionDef]:
        collect((tree.name, tree))
        stop()
    if type(tree) is Assign:
        for x in find_names.collect(tree.targets):
            collect(x)


def extract_arg_names(args):
    return dict(
        ([(args.vararg, args.vararg)] if args.vararg else []) +
        ([(args.kwarg, args.kwarg)] if args.kwarg else []) +
        [pair for x in args.args for pair in find_names.collect(x)]
    )


def with_scope(walker):



    walker.prep = lambda tree: dict(scope=dict(find_assignments.collect(tree)))
    old_func = walker.func

    def new_func(tree, set_ctx, set_ctx_for, scope={}, **kw):

        def extend_scope(tree, *dicts):
            set_ctx_for(tree, scope=merge_dicts(*([scope] + list(dicts))))

        if type(tree) is Lambda:
            extend_scope(tree.body, extract_arg_names(tree.args))

        if type(tree) in (GeneratorExp, ListComp, SetComp, DictComp):
            iterator_vars = {}
            for gen in tree.generators:
                extend_scope(gen.target, iterator_vars)
                extend_scope(gen.iter, iterator_vars)
                iterator_vars.update(dict(find_names.collect(gen.target)))
                extend_scope(gen.ifs, iterator_vars)

            if type(tree) is DictComp:
                extend_scope(tree.key, iterator_vars)
                extend_scope(tree.value, iterator_vars)
            else:
                extend_scope(tree.elt, iterator_vars)

        if type(tree) is FunctionDef:

            extend_scope(tree.args, {tree.name: tree})
            new_scope = merge_dicts(
                scope,
                {tree.name: tree},
                extract_arg_names(tree.args),
                dict(find_assignments.collect(tree.body)),
            )

            set_ctx_for(tree.body, scope=new_scope)

        if type(tree) is ClassDef:
            extend_scope(tree.body, dict(find_assignments.collect(tree.body)))

        if type(tree) is ExceptHandler:
            extend_scope(tree.body, {tree.name.id: tree.name})

        if type(tree) is For:
            extend_scope(tree.body, dict(find_names.collect(tree.target)))

        return old_func(tree, set_ctx_for=set_ctx_for, scope=scope, **kw)

    walker.func = new_func
    return walker