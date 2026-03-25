import csv
import os
import tempfile
import unittest
from pathlib import Path

import ezdxf

from cad_toolkit_gui import SolidEdgeNestingWorker


def _run_worker(input_file: str, output_dir: str):
    worker = SolidEdgeNestingWorker(
        input_file,
        output_dir,
        use_quantity_text=True,
        default_quantity=1,
        nesting_exe_path=None,
        auto_launch=False,
    )
    results = []
    logs = []
    worker.finished.connect(lambda success, message: results.append((success, message)))
    worker.progress.connect(logs.append)
    worker.run()
    return results, logs


def _collect_csv_rows(output_dir: str):
    rows = []
    for root, _, files in os.walk(output_dir):
        for file_name in files:
            if file_name.endswith(".csv"):
                csv_path = os.path.join(root, file_name)
                with open(csv_path, "r", encoding="mbcs", newline="") as handle:
                    rows.extend(list(csv.reader(handle)))
    return rows


def _collect_exported_dxfs(output_dir: str):
    exported = []
    for root, _, files in os.walk(output_dir):
        for file_name in files:
            if file_name.lower().endswith(".dxf"):
                exported.append(os.path.join(root, file_name))
    return sorted(exported)


class TestSolidEdgeNestingWorker(unittest.TestCase):
    def test_worker_fails_when_no_parts_exported(self):
        with tempfile.TemporaryDirectory(prefix="nest_worker_") as temp_dir:
            input_path = os.path.join(temp_dir, "empty.dxf")
            output_dir = os.path.join(temp_dir, "out")
            os.makedirs(output_dir, exist_ok=True)

            doc = ezdxf.new("R2010")
            doc.saveas(input_path)

            results, _ = _run_worker(input_path, output_dir)

            self.assertEqual(1, len(results))
            success, message = results[0]
            self.assertFalse(success)
            self.assertIn("未导出任何部件", message)
            self.assertEqual([], _collect_csv_rows(output_dir))
            self.assertEqual([], _collect_exported_dxfs(output_dir))

    def test_worker_aggregates_repeated_same_part_into_single_csv_row(self):
        with tempfile.TemporaryDirectory(prefix="nest_worker_") as temp_dir:
            input_path = os.path.join(temp_dir, "merged.dxf")
            output_dir = os.path.join(temp_dir, "out")
            os.makedirs(output_dir, exist_ok=True)

            doc = ezdxf.new("R2010")
            msp = doc.modelspace()
            msp.add_text("材质: SUS304", dxfattribs={"insert": (0, 1000)})
            msp.add_text("厚度: 2", dxfattribs={"insert": (0, 980)})

            block = doc.blocks.new("PART")
            block.add_line((0, 0), (10, 0))
            block.add_text("12345678", dxfattribs={"insert": (1, 1)})
            block.add_text("PARTA", dxfattribs={"insert": (1, 3)})

            msp.add_blockref("PART", (100, 100))
            msp.add_blockref("PART", (300, 100))
            doc.saveas(input_path)

            results, _ = _run_worker(input_path, output_dir)

            self.assertTrue(results[0][0], results[0][1])
            rows = _collect_csv_rows(output_dir)
            self.assertEqual(1, len(rows))
            self.assertEqual("2", rows[0][2])

            exported_dxfs = _collect_exported_dxfs(output_dir)
            self.assertEqual(1, len(exported_dxfs))

    def test_worker_uses_stable_distinct_names_for_different_parts_with_same_metadata(self):
        with tempfile.TemporaryDirectory(prefix="nest_worker_") as temp_dir:
            input_path = os.path.join(temp_dir, "merged.dxf")

            def build_input():
                doc = ezdxf.new("R2010")
                msp = doc.modelspace()
                msp.add_text("材质: SUS304", dxfattribs={"insert": (0, 1000)})
                msp.add_text("厚度: 2", dxfattribs={"insert": (0, 980)})

                block1 = doc.blocks.new("B1")
                block1.add_line((0, 0), (10, 0))
                block1.add_text("12345678", dxfattribs={"insert": (1, 1)})
                block1.add_text("PARTA", dxfattribs={"insert": (1, 3)})

                block2 = doc.blocks.new("B2")
                block2.add_circle((5, 5), 5)
                block2.add_text("12345678", dxfattribs={"insert": (1, 1)})
                block2.add_text("PARTA", dxfattribs={"insert": (1, 3)})

                msp.add_blockref("B1", (100, 100))
                msp.add_blockref("B2", (300, 100))
                doc.saveas(input_path)

            build_input()

            output_a = os.path.join(temp_dir, "out_a")
            output_b = os.path.join(temp_dir, "out_b")
            os.makedirs(output_a, exist_ok=True)
            os.makedirs(output_b, exist_ok=True)

            result_a, _ = _run_worker(input_path, output_a)
            result_b, _ = _run_worker(input_path, output_b)

            self.assertTrue(result_a[0][0], result_a[0][1])
            self.assertTrue(result_b[0][0], result_b[0][1])

            rows_a = sorted(row[0] for row in _collect_csv_rows(output_a))
            rows_b = sorted(row[0] for row in _collect_csv_rows(output_b))

            self.assertEqual(2, len(rows_a))
            self.assertEqual(rows_a, rows_b)
            self.assertEqual(2, len(set(rows_a)))

            exported_a = _collect_exported_dxfs(output_a)
            self.assertEqual(2, len(exported_a))


if __name__ == "__main__":
    unittest.main()
