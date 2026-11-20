"""Uji adaptasi format hasil tersimpan tanpa menjalankan model atau batch."""
import copy
import unittest
from uji_testing_tersimpan import adapt_predictions


class TestSavedPredictionAdapter(unittest.TestCase):
    def test_preserves_numerical_values_masks_and_original_order(self):
        row={"image_id":17,"category_id":2,"score":.91,"bbox_xyxy":[1.5,2.0,30.0,40.0],
             "segmentation":{"size":[50,50],"counts":"fixture"}}
        original=copy.deepcopy(row)
        out=adapt_predictions([(99,row)],{2:"ina_ma"})
        self.assertEqual(row,original)
        self.assertTrue(all(out[0][k]==v for k,v in row.items()))
        self.assertEqual(out[0]["instance_id"],1)
        self.assertEqual(out[0]["class_label"],"ina_ma")
        out[0]["segmentation"]["counts"]="changed_copy"
        self.assertEqual(row["segmentation"]["counts"],"fixture")

    def test_threshold_keeps_below_threshold_records(self):
        rows=[(0,{"category_id":0,"score":.49}),(1,{"category_id":0,"score":.5})]
        out=adapt_predictions(rows,{0:"ina_a"})
        self.assertEqual(len(out),2)
        self.assertEqual([p["displayed"] for p in out],[False,True])
        self.assertEqual([p["instance_id"] for p in out],[1,2])

    def test_empty_image_returns_empty_list(self):
        self.assertEqual(adapt_predictions([],{0:"ina_a"}),[])


if __name__=="__main__":unittest.main(verbosity=2)
