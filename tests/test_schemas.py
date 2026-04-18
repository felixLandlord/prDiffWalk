import pytest


class TestSchemas:
    def test_entity_ref(self):
        from pr_diff_walk.schemas import EntityRef

        ref = EntityRef(file_path="test.js", name="add", kind="function")
        assert ref.file_path == "test.js"
        assert ref.name == "add"
        assert ref.kind == "function"

    def test_entity_def(self):
        from pr_diff_walk.schemas import EntityDef

        entity = EntityDef(name="add", kind="function", start=1, end=5)
        assert entity.name == "add"
        assert entity.start == 1
        assert entity.end == 5
        assert entity.parent is None

    def test_import_edge(self):
        from pr_diff_walk.schemas import ImportEdge

        edge = ImportEdge(
            importer_file="main.js",
            source_file="utils.js",
            imported_name="add",
            alias="add",
            line_no=1,
            lang="js",
        )
        assert edge.importer_file == "main.js"
        assert edge.source_file == "utils.js"
        assert edge.line_no == 1

    def test_hop(self):
        from pr_diff_walk.schemas import Hop, EntityRef

        ref = EntityRef(file_path="test.js", name="add", kind="function")
        hop = Hop(
            depth=1,
            from_entity=ref,
            importer_file="main.js",
            imported_as="add",
            line_no=1,
            context_name="main",
            context_kind="function",
            snippet="line 1",
            snippet_start=1,
            snippet_end=1,
            next_entity=ref,
        )
        assert hop.depth == 1
        assert hop.context_name == "main"

    def test_changed_entity(self):
        from pr_diff_walk.schemas import ChangedEntity, EntityRef

        ref = EntityRef(file_path="test.js", name="add", kind="function")
        changed = ChangedEntity(entity=ref, from_patch_lines=[1, 2, 3])
        assert len(changed.from_patch_lines) == 3

    def test_dependency_chain(self):
        from pr_diff_walk.schemas import DependencyChain, EntityRef

        ref = EntityRef(file_path="test.js", name="add", kind="function")
        chain = DependencyChain(seed=ref, hops=[], terminals=[])
        assert chain.seed == ref
        assert len(chain.hops) == 0

    def test_language_config(self):
        from pr_diff_walk.schemas import LanguageConfig

        config = LanguageConfig(
            name="javascript",
            extensions={".js", ".jsx"},
            file_patterns=["*.js"],
            module_marker="<module>",
            package_indicator="",
            import_patterns={},
            entity_kinds={"function", "class"},
        )
        assert config.name == "javascript"
        assert ".js" in config.extensions

    def test_repository_files(self, temp_repo_dir):
        from pr_diff_walk.schemas import RepositoryFiles

        repo = RepositoryFiles(root=temp_repo_dir)
        assert repo.root == temp_repo_dir
        assert len(repo.repo_files) == 0
        assert ".git" in repo.excluded_dirs
