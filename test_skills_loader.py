"""Test suite for the SkillsLoader functionality."""

import os
import tempfile
from pathlib import Path

from coding_agent.core.skills_loader import SkillsLoader, load_skills_context


class TestSkillsLoader:
    """Tests for SkillsLoader class."""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        loader = SkillsLoader()
        assert loader.workspace_dir == Path(".").resolve()
        assert loader.skills_dirs == ['skills', 'rules', '.agent']
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        loader = SkillsLoader(workspace_dir="/tmp", skills_dirs=['custom'])
        assert loader.workspace_dir == Path("/tmp").resolve()
        assert loader.skills_dirs == ['custom']
    
    def test_find_skill_files_empty_directory(self):
        """Test finding skill files in empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = SkillsLoader(workspace_dir=tmpdir)
            files = loader.find_skill_files()
            assert len(files) == 0
    
    def test_find_skill_files_in_skills_directory(self):
        """Test finding skill files in skills/ directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / "skills"
            skills_dir.mkdir()
            
            # Create skill files
            (skills_dir / "python.md").write_text("# Python")
            (skills_dir / "javascript.md").write_text("# JavaScript")
            
            loader = SkillsLoader(workspace_dir=tmpdir)
            files = loader.find_skill_files()
            
            assert len(files) == 2
            assert all(f.suffix == ".md" for f in files)
    
    def test_find_skill_files_in_rules_directory(self):
        """Test finding skill files in rules/ directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir) / "rules"
            rules_dir.mkdir()
            
            (rules_dir / "security.md").write_text("# Security Rules")
            
            loader = SkillsLoader(workspace_dir=tmpdir)
            files = loader.find_skill_files()
            
            assert len(files) == 1
    
    def test_find_skill_files_in_agent_directory(self):
        """Test finding skill files in .agent/ directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / ".agent"
            agent_dir.mkdir()
            
            (agent_dir / "custom.md").write_text("# Custom Rules")
            
            loader = SkillsLoader(workspace_dir=tmpdir)
            files = loader.find_skill_files()
            
            assert len(files) == 1
    
    def test_find_skill_files_excludes_readme(self):
        """Test that README.md is excluded from root directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "README.md").write_text("# README")
            (Path(tmpdir) / "skills_guide.md").write_text("# Skills Guide")
            
            loader = SkillsLoader(workspace_dir=tmpdir)
            files = loader.find_skill_files()
            
            # README should be excluded, skills_guide should be included
            assert len(files) == 1
            assert "skills_guide.md" in str(files[0])
    
    def test_load_skill_content(self):
        """Test loading content from a single file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "test.md"
            skill_file.write_text("# Test Content\n\nSome text here.")
            
            loader = SkillsLoader(workspace_dir=tmpdir)
            content = loader.load_skill_content(skill_file)
            
            assert "# Test Content" in content
            assert "Some text here" in content
    
    def test_load_all_skills(self):
        """Test loading all skills from multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / "skills"
            skills_dir.mkdir()
            
            (skills_dir / "skill1.md").write_text("# Skill 1")
            (skills_dir / "skill2.md").write_text("# Skill 2")
            
            loader = SkillsLoader(workspace_dir=tmpdir)
            skills = loader.load_all_skills()
            
            assert len(skills) == 2
            assert "skills/skill1.md" in skills
            assert "skills/skill2.md" in skills
    
    def test_format_for_context(self):
        """Test formatting skills for LLM context."""
        skills = {
            "test.md": "# Test\n\nContent here"
        }
        
        loader = SkillsLoader()
        context = loader.format_for_context(skills)
        
        assert "SKILLS AND RULES CONTEXT" in context
        assert "Source: test.md" in context
        assert "# Test" in context
        assert "END OF SKILLS AND RULES" in context
    
    def test_format_for_context_empty(self):
        """Test formatting with empty skills dict."""
        loader = SkillsLoader()
        context = loader.format_for_context({})
        
        assert context == ""
    
    def test_get_skills_context_with_files(self):
        """Test getting skills context when files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / "skills"
            skills_dir.mkdir()
            (skills_dir / "test.md").write_text("# Test")
            
            loader = SkillsLoader(workspace_dir=tmpdir)
            context = loader.get_skills_context()
            
            assert context is not None
            assert "SKILLS AND RULES CONTEXT" in context
    
    def test_get_skills_context_no_files(self):
        """Test getting skills context when no files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = SkillsLoader(workspace_dir=tmpdir)
            context = loader.get_skills_context()
            
            assert context is None
    
    def test_load_skills_context_function(self):
        """Test the convenience function load_skills_context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / "skills"
            skills_dir.mkdir()
            (skills_dir / "test.md").write_text("# Test")
            
            context = load_skills_context(workspace_dir=tmpdir)
            
            assert context is not None
            assert "SKILLS AND RULES CONTEXT" in context


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
