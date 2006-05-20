try:
    import pkg_resources
    pkg_resources.declare_namespace('schevo')
except ImportError:
    pass
