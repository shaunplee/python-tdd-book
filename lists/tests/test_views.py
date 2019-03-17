from lists.forms import (ExistingListItemForm, ItemForm,
                         DUPLICATE_ITEM_ERROR, EMPTY_ITEM_ERROR)
from lists.models import Item, List
from lists.views import home_page, new_list, user_not_found_string, view_list

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import TestCase
from django.urls import resolve
from django.utils.html import escape

from unittest.mock import patch, Mock
import unittest

User = get_user_model()

class HomePageTest(TestCase):
    def test_root_url_resolves_to_home_page_view(self):
        found = resolve('/')
        self.assertEqual(found.func, home_page)

    def test_home_page_returns_correct_html(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')

    def test_home_page_uses_item_form(self):
        response = self.client.get('/')
        self.assertIsInstance(response.context['form'], ItemForm)


class ListViewTest(TestCase):

    def test_uses_list_template(self):
        list_ = List.objects.create()
        response = self.client.get(f'/lists/{list_.id}/')
        self.assertTemplateUsed(response, 'list.html')

    def test_displays_only_items_for_that_list(self):
        correct_list = List.objects.create()
        Item.objects.create(text='itemey 1', list=correct_list)
        Item.objects.create(text='itemey 2', list=correct_list)
        other_list = List.objects.create()
        Item.objects.create(text='other list item 1', list=other_list)
        Item.objects.create(text='other list item 2', list=other_list)

        response = self.client.get(f'/lists/{correct_list.id}/')

        self.assertContains(response, 'itemey 1')
        self.assertContains(response, 'itemey 2')
        self.assertNotContains(response, 'other list item 1')
        self.assertNotContains(response, 'other list item 2')

    def test_passes_correct_list_to_template(self):
        other_list = List.objects.create()
        correct_list = List.objects.create()
        response = self.client.get(f'/lists/{correct_list.id}/')
        self.assertEqual(response.context['list'], correct_list)

    def test_can_save_a_POST_request_to_an_existing_list(self):
        other_list = List.objects.create()
        correct_list = List.objects.create()

        self.client.post(
            f'/lists/{correct_list.id}/',
            data={'text': 'A new item for an existing list'})

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new item for an existing list')
        self.assertEqual(new_item.list, correct_list)

    def test_redirects_to_list_view(self):
        other_list = List.objects.create()
        correct_list = List.objects.create()

        response = self.client.post(
            f'/lists/{correct_list.id}/',
            data={'text': 'A new item for an existing list'}
        )

        self.assertRedirects(response, f'/lists/{correct_list.id}/')

    def post_invalid_input(self):
        list_ = List.objects.create()
        return self.client.post(f'/lists/{list_.id}/',
                                data={'text': ''})

    def test_for_invalid_input_nothing_saved_to_db(self):
        self.post_invalid_input()
        self.assertEqual(Item.objects.count(), 0)

    def test_for_invalid_input_renders_list_template(self):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'list.html')

    def test_for_invalid_input_passes_form_to_template(self):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context['form'], ExistingListItemForm)

    def test_for_invalid_input_shows_error_on_page(self):
        response = self.post_invalid_input()
        self.assertContains(response, escape(EMPTY_ITEM_ERROR))

    def test_displays_item_form(self):
        list_ = List.objects.create()
        response = self.client.get(f'/lists/{list_.id}/')
        self.assertIsInstance(response.context['form'], ExistingListItemForm)
        self.assertContains(response, 'name="text"')

    def test_duplicate_item_validation_errors_end_up_on_lists_page(self):
        list1 = List.objects.create()
        item1 = Item.objects.create(list=list1, text='textey')
        response = self.client.post(
            f'/lists/{list1.id}/',
            data={'text': 'textey'})

        expected_error = escape(DUPLICATE_ITEM_ERROR)
        self.assertContains(response, expected_error)
        self.assertTemplateUsed(response, 'list.html')
        self.assertEqual(Item.objects.all().count(), 1)


class NewListViewIntegratedTest(TestCase):

    def test_can_save_a_POST_request(self):
        self.client.post(
            '/lists/new', data={'text': 'A new list item'})
        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new list item')

    def test_redirects_after_POST(self):
        response = self.client.post(
            '/lists/new', data={'text': 'A new list item'})
        new_list = List.objects.first()
        self.assertRedirects(
            response, f'/lists/{new_list.id}/')

    def test_for_invalid_input_renders_home_template(self):
        response = self.client.post('/lists/new', data={'text': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_validation_errors_are_shown_on_home_page(self):
        response = self.client.post('/lists/new', data={'text': ''})
        self.assertContains(response, escape(EMPTY_ITEM_ERROR))

    def test_for_invalid_input_passes_form_to_template(self):
        response = self.client.post('/lists/new', data={'text': ''})
        self.assertIsInstance(response.context['form'], ItemForm)

    def test_invalid_list_items_arent_saved(self):
        self.client.post('/lists/new', data={'text': ''})
        self.assertEqual(List.objects.count(), 0)
        self.assertEqual(Item.objects.count(), 0)

    def test_list_owner_is_saved_if_user_is_authenticated(self):
        user = User.objects.create(email='a@b.com')
        self.client.force_login(user)
        self.client.post('/lists/new', data={'text': 'new item'})
        list_ = List.objects.first()
        self.assertEqual(list_.owner, user)


class MyListsTest(TestCase):

    def test_my_lists_url_renders_my_lists_template(self):
        User.objects.create(email='a@b.com')
        response = self.client.get('/lists/users/a@b.com/')
        self.assertTemplateUsed(response, 'my_lists.html')

    def test_passes_correct_owner_to_template(self):
        User.objects.create(email='wrong@owner.com')
        correct_user = User.objects.create(email='a@b.com')
        response = self.client.get('/lists/users/a@b.com/')
        self.assertEqual(response.context['owner'], correct_user)

@patch('lists.views.NewListForm')
class NewListViewUnitTest(unittest.TestCase):
    def setUp(self):
        self.request = HttpRequest()
        self.request.POST['text'] = 'new list item'
        self.request.user = Mock()

    def test_passes_POST_data_to_NewListForm(self, mockNewListForm):
        new_list(self.request)
        mockNewListForm.assert_called_once_with(data=self.request.POST)

    def test_saves_form_with_owner_if_form_valid(self, mockNewListForm):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value
        new_list(self.request)
        mock_form.save.assert_called_once_with(owner=self.request.user)

    @patch('lists.views.redirect')
    def test_redirects_to_form_returned_object_if_form_valid(
            self, mock_redirect, mockNewListForm
    ):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = True

        response = new_list(self.request)

        self.assertEqual(response, mock_redirect.return_value)
        mock_redirect.assert_called_once_with(mock_form.save.return_value)

    @patch('lists.views.render')
    def test_renders_home_template_with_form_if_form_invalid(
            self, mock_render, mockNewListForm
    ):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = False

        response = new_list(self.request)

        self.assertEqual(response, mock_render.return_value)
        mock_render.assert_called_once_with(
            self.request, 'home.html', {'form': mock_form}
        )

    def test_does_not_save_if_form_invalid(self, mockNewListForm):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = False
        new_list(self.request)
        self.assertFalse(mock_form.save.called)


class ShareListTest(TestCase):
    """
    Unit tests for list sharing features.
    """

    def setUp(self):
        self.request = HttpRequest()
        self.request.POST['text'] = 'new list item'
        self.request.user = User.objects.create(email='a@b.com')
        new_list(self.request)
        self.list = List.objects.first()

    def test_post_redirects_to_lists_page(self):
        response = self.client.post(
            f'/lists/{self.list.id}/share',
            data={'list_id': self.list.id,
                  'sharee': self.request.user.email}
        )
        self.assertRedirects(response, f'/lists/{self.list.id}/')

    def test_add_list_owner_to_shared_with(self):
        self.client.post(f'/lists/{self.list.id}/share',
                          data={'list_id': self.list.id,
                                'sharee': self.request.user.email}
        )
        self.assertIn(self.request.user, self.list.shared_with.all())

    def test_add_another_user_to_shared_with(self):
        sharee = User.objects.create(email="cherie@example.com")
        self.client.post(f'/lists/{self.list.id}/share',
                          data={'list_id': self.list.id,
                                'sharee': sharee.email}
        )
        self.assertIn(sharee, self.list.shared_with.all())

    def test_add_invalid_user_to_shared_with_shows_error(self):
        invalid_user_email = "invalid_user@example.com"
        response = self.client.post(f'/lists/{self.list.id}/share',
                                    data={'list_id': self.list.id,
                                          'sharee': invalid_user_email}
        )
        self.assertContains(response,
                            escape(user_not_found_string(invalid_user_email)))

    def test_add_invalid_user_to_shared_with_has_no_effect(self):
        num_prev_shared_with = len(self.list.shared_with.all())
        self.client.post(f'/lists/{self.list.id}/share',
                         data={'list_id': self.list.id,
                               'sharee': "dogggg@example.com"}
        )
        self.assertEqual(num_prev_shared_with, len(self.list.shared_with.all()))

    def test_list_view_shows_shared_with_users(self):
        sharee = User.objects.create(email="cherie@example.com")
        self.client.post(f'/lists/{self.list.id}/share',
                         data={'list_id': self.list.id,
                               'sharee': sharee.email})
        response = self.client.get(f'/lists/{self.list.id}', follow=True)
        self.assertContains(response, escape(sharee.email))

    def test_shared_with_user_can_add_to_list(self):
        sharee = User.objects.create(email="cherie@example.com")
        self.client.post(f'/lists/{self.list.id}/share',
                         data={'list_id': self.list.id,
                               'sharee': sharee.email})
        sharee_request = HttpRequest()
        sharee_request.user = sharee
        sharee_request.method = 'POST'
        sharee_request.POST['text'] = "sharee item"
        # POST new item
        view_list(sharee_request, self.list.id)
        response = self.client.get(f'/lists/{self.list.id}', follow=True)
        self.assertContains(response, escape("sharee item"))

    def test_not_shared_with_user_cannot_add_to_list(self):
        not_sharee_request = HttpRequest()
        not_sharee_request.user = User.objects.create(
            email="notcherie@example.com")
        not_sharee_request.method = 'POST'
        not_sharee_request.POST['text'] = "sharee item"
        # POST new item
        view_list(not_sharee_request, self.list.id)
        response = self.client.get(f'/lists/{self.list.id}', follow=True)
        self.assertNotContains(response, escape("sharee item"))
