"""
Tests for tool_registry — ToolSpec, ToolRegistry, and decorator-based registration.
"""
import pytest

from tool_registry import ToolRegistry, ToolSpec, _py_type_name, ORIGIN_SIGNATURE


# ─── _py_type_name ────────────────────────────────────────────────────────────

class TestPyTypeName:
    def test_known_types(self):
        assert _py_type_name(int) == "integer"
        assert _py_type_name(float) == "number"
        assert _py_type_name(str) == "string"
        assert _py_type_name(bool) == "boolean"
        assert _py_type_name(list) == "array"
        assert _py_type_name(dict) == "object"

    def test_unknown_type(self):
        assert _py_type_name(bytes) == "any"


# ─── ToolSpec ─────────────────────────────────────────────────────────────────

class TestToolSpec:
    def _make_spec(self):
        def add(a: int, b: int) -> int:
            return a + b
        return ToolSpec("add", add, "Add two integers", {"a": int, "b": int})

    def test_schema_structure(self):
        spec = self._make_spec()
        schema = spec.schema()
        assert schema["name"] == "add"
        assert "description" in schema
        assert "parameters" in schema
        props = schema["parameters"]["properties"]
        assert props["a"]["type"] == "integer"
        assert props["b"]["type"] == "integer"

    def test_schema_required_params(self):
        spec = self._make_spec()
        schema = spec.schema()
        assert set(schema["parameters"]["required"]) == {"a", "b"}

    def test_validate_ok(self):
        spec = self._make_spec()
        assert spec.validate({"a": 1, "b": 2}) is None

    def test_validate_missing_param(self):
        spec = self._make_spec()
        err = spec.validate({"a": 1})
        assert err is not None
        assert "missing" in err

    def test_validate_wrong_type(self):
        spec = self._make_spec()
        err = spec.validate({"a": "one", "b": 2})
        assert err is not None
        assert "expected" in err

    def test_validate_int_to_float_coercion(self):
        def mul(a: float, b: float) -> float:
            return a * b
        spec = ToolSpec("mul", mul, "Multiply", {"a": float, "b": float})
        # int values should pass for float params
        assert spec.validate({"a": 2, "b": 3}) is None

    def test_schema_with_dict_spec(self):
        def tool(x):
            pass
        spec = ToolSpec("t", tool, "desc", {"x": {"type": "string", "enum": ["a", "b"]}})
        schema = spec.schema()
        assert schema["parameters"]["properties"]["x"]["enum"] == ["a", "b"]


# ─── ToolRegistry ─────────────────────────────────────────────────────────────

class TestToolRegistry:
    @pytest.fixture
    def reg(self):
        return ToolRegistry()

    def test_register_decorator(self, reg):
        @reg.register(description="Echo", parameters={"msg": str})
        def echo(msg: str) -> str:
            return msg

        assert "echo" in reg.list_tools()

    def test_register_uses_fn_name(self, reg):
        @reg.register(description="No-op")
        def my_tool():
            pass

        assert "my_tool" in reg.list_tools()

    def test_register_custom_name(self, reg):
        @reg.register(name="custom", description="Custom name")
        def fn():
            pass

        assert "custom" in reg.list_tools()
        assert "fn" not in reg.list_tools()

    def test_add_non_decorator(self, reg):
        def double(x: int) -> int:
            return x * 2
        reg.add(double, description="Double", parameters={"x": int})
        assert "double" in reg.list_tools()

    def test_list_tools_sorted(self, reg):
        @reg.register(description="z")
        def z_tool():
            pass

        @reg.register(description="a")
        def a_tool():
            pass

        names = reg.list_tools()
        assert names == sorted(names)

    def test_get_schema_known(self, reg):
        @reg.register(description="Echo", parameters={"msg": str})
        def echo(msg: str) -> str:
            return msg

        schema = reg.get_schema("echo")
        assert schema is not None
        assert schema["name"] == "echo"

    def test_get_schema_unknown(self, reg):
        assert reg.get_schema("nonexistent") is None

    def test_all_schemas(self, reg):
        @reg.register(description="A")
        def tool_a():
            pass

        @reg.register(description="B")
        def tool_b():
            pass

        schemas = reg.all_schemas()
        assert len(schemas) == 2

    def test_remove_existing(self, reg):
        @reg.register(description="temp")
        def temp():
            pass

        assert reg.remove("temp") is True
        assert "temp" not in reg.list_tools()

    def test_remove_nonexistent(self, reg):
        assert reg.remove("nope") is False

    def test_call_success(self, reg):
        @reg.register(description="Add", parameters={"a": int, "b": int})
        def add(a: int, b: int) -> int:
            return a + b

        result = reg.call("add", {"a": 3, "b": 4})
        assert result["ok"] is True
        assert result["output"] == 7
        assert result["error"] is None

    def test_call_unknown_tool(self, reg):
        result = reg.call("nope")
        assert result["ok"] is False
        assert "not registered" in result["error"]

    def test_call_validation_error(self, reg):
        @reg.register(description="Echo", parameters={"msg": str})
        def echo(msg: str) -> str:
            return msg

        result = reg.call("echo", {})
        assert result["ok"] is False
        assert "validation error" in result["error"]

    def test_call_exception_captured(self, reg):
        @reg.register(description="Boom")
        def boom():
            raise RuntimeError("intentional error")

        result = reg.call("boom", {})
        assert result["ok"] is False
        assert "RuntimeError" in result["error"]

    def test_call_record_fields(self, reg):
        @reg.register(description="No-op")
        def noop():
            pass

        result = reg.call("noop", {})
        for key in ("tool", "input", "output", "error", "ok", "elapsed_ms", "called_at_ms", "origin_signature"):
            assert key in result

    def test_call_origin_signature(self, reg):
        @reg.register(description="No-op")
        def noop():
            pass

        result = reg.call("noop", {})
        assert result["origin_signature"] == ORIGIN_SIGNATURE

    def test_call_log_grows(self, reg):
        @reg.register(description="No-op")
        def noop():
            pass

        reg.call("noop")
        reg.call("noop")
        assert len(reg.call_log()) == 2

    def test_call_log_returns_copy(self, reg):
        @reg.register(description="No-op")
        def noop():
            pass

        reg.call("noop")
        log = reg.call_log()
        log.clear()
        assert len(reg.call_log()) == 1

    def test_infer_params_from_annotations(self, reg):
        @reg.register(description="Typed fn")
        def typed(x: int, y: str) -> str:
            return y * x

        schema = reg.get_schema("typed")
        props = schema["parameters"]["properties"]
        assert props["x"]["type"] == "integer"
        assert props["y"]["type"] == "string"
