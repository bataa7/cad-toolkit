import tempfile
import unittest
from pathlib import Path

import ezdxf

from block_creator import BlockCreator


class TestBlockCreatorCleanup(unittest.TestCase):
    def setUp(self):
        self.creator = BlockCreator()

    def test_clear_existing_blocks_preserves_dimension_anonymous_block(self):
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        dimension = msp.add_linear_dim(base=(0, 5), p1=(0, 0), p2=(10, 0), angle=0)
        dimension.render()
        anonymous_block_name = dimension.dimension.dxf.geometry

        self.creator._clear_existing_blocks(doc)

        self.assertIn(anonymous_block_name, doc.blocks)

    def test_process_cad_file_same_name_conflict_keeps_new_content(self):
        with tempfile.TemporaryDirectory(prefix="cad_cleanup_") as temp_dir:
            input_path = Path(temp_dir) / "same_name_input.dxf"
            output_path = Path(temp_dir) / "same_name_output.dxf"

            doc = ezdxf.new("R2010")
            msp = doc.modelspace()
            old_block = doc.blocks.new(name="SAME")
            old_block.add_circle((1, 1), 2)
            msp.add_blockref("SAME", (20, 20))
            msp.add_text("SAME", dxfattribs={"insert": (0, 0)})
            msp.add_line((0, 0), (10, 0))
            doc.saveas(input_path)

            result = self.creator.process_cad_file(
                str(input_path),
                output_file=str(output_path),
                text_strategy="first_valid",
                clear_existing_blocks=True,
            )

            self.assertEqual(str(output_path), result)

            output_doc = ezdxf.readfile(output_path)
            inserts = [entity for entity in output_doc.modelspace() if entity.dxftype() == "INSERT"]
            self.assertEqual(1, len(inserts))

            new_block_name = inserts[0].dxf.name
            self.assertNotEqual("SAME", new_block_name)

            new_block = output_doc.blocks.get(new_block_name)
            new_block_entity_types = {entity.dxftype() for entity in new_block}
            self.assertIn("LINE", new_block_entity_types)
            self.assertIn("TEXT", new_block_entity_types)
            self.assertIn("INSERT", new_block_entity_types)

            old_block_after = output_doc.blocks.get("SAME")
            self.assertEqual(["CIRCLE"], [entity.dxftype() for entity in old_block_after])

    def test_process_cad_file_purges_unreachable_blocks_and_restores_name(self):
        with tempfile.TemporaryDirectory(prefix="cad_cleanup_") as temp_dir:
            input_path = Path(temp_dir) / "purge_input.dxf"
            output_path = Path(temp_dir) / "purge_output.dxf"

            doc = ezdxf.new("R2010")
            msp = doc.modelspace()

            conflict_block = doc.blocks.new(name="TARGET")
            conflict_block.add_circle((0, 0), 1)

            orphan_parent = doc.blocks.new(name="ORPHAN_A")
            orphan_child = doc.blocks.new(name="ORPHAN_B")
            orphan_parent.add_blockref("ORPHAN_B", (0, 0))
            orphan_child.add_line((0, 0), (2, 0))

            msp.add_text("TARGET", dxfattribs={"insert": (0, 0)})
            msp.add_line((0, 0), (5, 0))
            doc.saveas(input_path)

            result = self.creator.process_cad_file(
                str(input_path),
                output_file=str(output_path),
                text_strategy="first_valid",
                clear_existing_blocks=True,
            )

            self.assertEqual(str(output_path), result)

            output_doc = ezdxf.readfile(output_path)
            inserts = [entity for entity in output_doc.modelspace() if entity.dxftype() == "INSERT"]
            self.assertEqual(["TARGET"], [entity.dxf.name for entity in inserts])

            self.assertNotIn("ORPHAN_A", output_doc.blocks)
            self.assertNotIn("ORPHAN_B", output_doc.blocks)

            final_block = output_doc.blocks.get("TARGET")
            final_block_entity_types = {entity.dxftype() for entity in final_block}
            self.assertIn("LINE", final_block_entity_types)
            self.assertIn("TEXT", final_block_entity_types)


if __name__ == "__main__":
    unittest.main()
