"""Blueprint helper that preserves RoastLogger's historic endpoint names."""

from __future__ import annotations


def register_unprefixed_routes(blueprint, routes) -> None:
    @blueprint.record_once
    def register(state):
        for route in routes:
            rule, endpoint, view_func, methods = route
            state.app.add_url_rule(
                rule,
                endpoint=endpoint,
                view_func=view_func,
                methods=methods,
            )
