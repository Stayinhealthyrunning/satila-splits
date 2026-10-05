#!/usr/bin/env python3
"""Regression contract for conservative source-aware sex normalization."""
from __future__ import annotations
import unittest

from tools.build_satila import normalized_sex


class SexNormalizationContract(unittest.TestCase):
    def test_agreeing_source_fields_are_preserved(self):
        self.assertEqual(normalized_sex({"Kjonn":"M"},{"Kjonn":"M","Navn":"Man"}),"M")
        self.assertEqual(normalized_sex({"Kjonn":"F"},{"Kjonn":"F","Navn":"Kvinna"}),"F")

    def test_explicit_conflicts_become_analytically_unknown(self):
        self.assertIsNone(normalized_sex({"Kjonn":"M"},{"Kjonn":"F","Navn":"Kvinna"}))
        self.assertIsNone(normalized_sex({"Kjonn":"F"},{"Kjonn":"M","Navn":"Man"}))

    def test_explicit_class_label_is_used_when_class_sex_field_is_missing(self):
        self.assertIsNone(normalized_sex({"Kjonn":"M"},{"Navn":"Kvinna"}))
        self.assertIsNone(normalized_sex({"Kjonn":"F"},{"Navn":"Herr 40"}))
        self.assertEqual(normalized_sex({},{"Navn":"Dam 50"}),"F")

    def test_non_gendered_class_names_do_not_invent_sex(self):
        self.assertEqual(normalized_sex({"Kjonn":"M"},{"Navn":"Motion 43 km"}),"M")
        self.assertIsNone(normalized_sex({},{"Navn":"Motion 43 km"}))


if __name__=="__main__":
    unittest.main(verbosity=2)
