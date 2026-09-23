"""测试 Plugin 基类。"""
import pytest

from verdant_generator.render_engine import OutputFile, Plugin


class SimplePlugin(Plugin):
    def __init__(self, template_path, combos):
        self._template_path = template_path
        self._combos = combos

    @property
    def name(self):
        return "simple"

    def template_path(self):
        return self._template_path

    def replacements(self):
        return self._combos


class TestPluginDefaultPipeline:
    def test_run_produces_expected_files(self, tmp_path):
        tpl = tmp_path / "{x}.txt"
        tpl.write_text("value: {x}", encoding="utf-8")

        plugin = SimplePlugin(template_path=str(tpl), combos=[{"x": "a"}, {"x": "b"}])
        outputs = plugin.run()

        assert len(outputs) == 2
        by_name = {f.filename: f.content for f in outputs}
        assert by_name["a.txt"] == "value: a"
        assert by_name["b.txt"] == "value: b"

    def test_plugin_can_override_post_processor(self, tmp_path):
        tpl = tmp_path / "out.txt"
        tpl.write_text("{x}", encoding="utf-8")

        class UpperPlugin(SimplePlugin):
            def post_processor(self):
                return lambda text, combo: text.upper()

        plugin = UpperPlugin(template_path=str(tpl), combos=[{"x": "hello"}])
        outputs = plugin.run()
        assert outputs[0].content == "HELLO"

    def test_empty_replacements(self, tmp_path):
        tpl = tmp_path / "out.txt"
        tpl.write_text("{x}", encoding="utf-8")

        plugin = SimplePlugin(template_path=str(tpl), combos=[])
        assert plugin.run() == []


class TestPluginAbstract:
    def test_cannot_instantiate_base_plugin(self):
        with pytest.raises(TypeError):
            Plugin()