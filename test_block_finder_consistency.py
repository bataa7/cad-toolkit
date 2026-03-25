import os
import tempfile
import unittest
from pathlib import Path

import ezdxf
import pandas as pd

from block_finder import BlockFinder


class TestBlockFinderConsistency(unittest.TestCase):
    def setUp(self):
        self.finder = BlockFinder()

    def test_identify_columns_prefers_exact_material_column(self):
        df = pd.DataFrame(
            columns=[
                "material_id",
                "drawing",
                "total qty",
                "material",
                "thickness",
                "name",
            ]
        )

        column_map = self.finder._identify_columns(df)

        self.assertEqual("material_id", column_map["material_id"])
        self.assertEqual("material", column_map["material"])
        self.assertNotEqual(column_map["material_id"], column_map["material"])

    def test_extract_material_info_uses_actual_material_column(self):
        df = pd.DataFrame(
            [
                {
                    "material_id": "ID1",
                    "drawing": "D1",
                    "total qty": 1,
                    "material": "M",
                    "thickness": "T1",
                    "name": "A",
                }
            ]
        )

        material_info = self.finder.extract_material_info(df)

        self.assertEqual("M", material_info["ID1"]["material"])
        self.assertEqual("M", material_info["D1"]["material"])

    def test_process_files_marks_merged_identifiers_in_excel(self):
        with tempfile.TemporaryDirectory(prefix="block_finder_consistency_") as temp_dir:
            temp_path = Path(temp_dir)
            excel_path = temp_path / "input.xlsx"
            dxf_path = temp_path / "source.dxf"
            output_dir = temp_path / "out"
            output_dir.mkdir()

            pd.DataFrame(
                [
                    {
                        "material_id": "ID1",
                        "drawing": "D1",
                        "total qty": 1,
                        "material": "M",
                        "thickness": "T1",
                        "name": "A",
                    },
                    {
                        "material_id": "ID2",
                        "drawing": "D2",
                        "total qty": 1,
                        "material": "M",
                        "thickness": "T1",
                        "name": "B",
                    },
                ]
            ).to_excel(excel_path, index=False)

            doc = ezdxf.new("R2010")
            block1 = doc.blocks.new("B1")
            block1.add_text("ID1", dxfattribs={"insert": (0, 0)})
            block1.add_line((0, 0), (10, 0))

            block2 = doc.blocks.new("B2")
            block2.add_text("ID2", dxfattribs={"insert": (0, 0)})
            block2.add_line((0, 0), (10, 0))
            doc.saveas(dxf_path)

            success = self.finder.process_files(
                str(excel_path),
                [str(dxf_path)],
                str(output_dir),
                attribs_config={
                    "material": True,
                    "thickness": True,
                    "material_id": True,
                    "drawing_num": True,
                    "name": True,
                    "total_qty": True,
                },
            )

            self.assertTrue(success)

            merged_doc = ezdxf.readfile(os.path.join(output_dir, "merged_blocks.dxf"))
            inserts = [entity for entity in merged_doc.modelspace() if entity.dxftype() == "INSERT"]
            self.assertEqual(1, len(inserts))

            insert_attribs = {attrib.dxf.tag: attrib.dxf.text for attrib in inserts[0].attribs}
            self.assertEqual("M", insert_attribs["材质"])
            self.assertEqual("ID1", insert_attribs["物料ID"])
            self.assertEqual("2", insert_attribs["总数量"])

            updated_df = pd.read_excel(os.path.join(output_dir, "updated_input.xlsx"))
            rows = {row["material_id"]: row for row in updated_df.to_dict("records")}

            self.assertEqual("已找到", rows["ID1"]["查找结果"])
            self.assertEqual("物料ID", rows["ID1"]["匹配类型"])
            self.assertTrue(pd.isna(rows["ID1"]["合并到标识符"]) or rows["ID1"]["合并到标识符"] == "")

            self.assertEqual("已合并", rows["ID2"]["查找结果"])
            self.assertEqual("物料ID", rows["ID2"]["匹配类型"])
            self.assertEqual("ID1", rows["ID2"]["合并到标识符"])


if __name__ == "__main__":
    unittest.main()
