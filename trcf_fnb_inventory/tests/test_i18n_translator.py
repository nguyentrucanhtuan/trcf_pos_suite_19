# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged

from ..i18n import get_translator, VI_TO_EN


class _FakeRequest:
    """Stand-in for odoo.http.request: get_translator only reads
    request.env.user.lang, so a lightweight namespace object is enough
    to exercise it outside of an actual HTTP request."""

    def __init__(self, env):
        self.env = env


@tagged('post_install', '-at_install', 'trcf_inventory')
class TestI18nTranslator(TransactionCase):

    def _translator_for_lang(self, lang):
        self.env.user.write({'lang': lang})
        return get_translator(_FakeRequest(self.env))

    def test_vietnamese_lang_passthrough(self):
        t = self._translator_for_lang('vi_VN')
        self.assertEqual(t('Nhập hàng'), 'Nhập hàng')

    def test_english_lang_translates_known_string(self):
        t = self._translator_for_lang('en_US')
        self.assertEqual(t('Nhập hàng'), 'Receiving')

    def test_english_lang_passes_through_unknown_string(self):
        t = self._translator_for_lang('en_US')
        unknown = 'Chuỗi này không có trong từ điển'
        self.assertEqual(t(unknown), unknown)

    def test_defaults_to_vietnamese_when_lang_unset(self):
        self.env.user.write({'lang': False})
        t = get_translator(_FakeRequest(self.env))
        self.assertEqual(t('Nhập hàng'), 'Nhập hàng')

    def test_dictionary_has_no_blank_entries(self):
        for vi_text, en_text in VI_TO_EN.items():
            self.assertTrue(vi_text.strip(), "VI_TO_EN has a blank Vietnamese key")
            self.assertTrue(en_text.strip(), f"VI_TO_EN[{vi_text!r}] has a blank English translation")
