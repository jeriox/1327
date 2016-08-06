from django.core.urlresolvers import reverse
from django_webtest import WebTest
from guardian.utils import get_anonymous_user
from model_mommy import mommy

from .models import UserProfile


class UsecaseTests(WebTest):
	extra_environ = {'HTTP_ACCEPT_LANGUAGE': 'en'}

	def setUp(self):
		self.user = mommy.make(
			UserProfile,
			username="user",
			password="pbkdf2_sha256$12000$uH9Cc7pBkaxQ$XLVGZKTbCyuDlgFQB65Mn5SAm6v/2kjpCTct1td2VTo=")
		mommy.make(UserProfile, username="noname")
		mommy.make(UserProfile, username="nofirstname", last_name="Last")
		mommy.make(UserProfile, username="nolastname", first_name="First")
		mommy.make(UserProfile, is_superuser=True, username="admin", first_name="Admin", last_name="User")

	def test_login(self):
		page = self.app.get("/login", user="")

		login_form = page.forms[0]
		login_form['username'] = "user"
		login_form['password'] = "wrong_password"
		self.assertIn("Please enter a correct username and password", login_form.submit())

		login_form = page.forms[0]
		login_form['username'] = "user"
		login_form['password'] = "test"

		self.assertEqual(login_form.submit().status_code, 302)

	def test_name(self):
		user = UserProfile.objects.get(username='noname')
		self.assertEqual(user.get_full_name(), 'noname')
		self.assertEqual(user.get_short_name(), 'noname')

		user = UserProfile.objects.get(username='nofirstname')
		self.assertEqual(user.get_full_name(), 'nofirstname')
		self.assertEqual(user.get_short_name(), 'nofirstname')

		user = UserProfile.objects.get(username='nolastname')
		self.assertEqual(user.get_full_name(), 'nolastname')
		self.assertEqual(user.get_short_name(), 'First')

		user = UserProfile.objects.get(username='admin')
		self.assertEqual(user.get_full_name(), 'Admin User')
		self.assertEqual(user.get_short_name(), 'Admin')


class UserImpersonationTests(WebTest):
	csrf_checks = False
	extra_environ = {'HTTP_ACCEPT_LANGUAGE': 'en'}

	def setUp(self):
		self.user = mommy.make(UserProfile, is_superuser=True)
		mommy.make(UserProfile, username='test')

	def test_view_impersonation_page(self):
		response = self.app.get(reverse('view_as'), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms['user_impersonation_form']
		options = [option[-1] for option in form['username'].options]
		self.assertIn('AnonymousUser', options)
		for user in UserProfile.objects.all():
			self.assertIn(user.username, options)

	def test_view_impersonation_list_no_superuser(self):
		user = mommy.make(UserProfile)
		response = self.app.get(reverse('view_as'), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)

	def test_impersonate_any_user(self):
		users = list(UserProfile.objects.all().exclude(username=self.user.username))
		users.append(get_anonymous_user())

		for user in users:
			response = self.app.post('/hijack/{user_id}/'.format(user_id=user.id), user=self.user)
			self.assertRedirects(response, reverse('index'))
			response = response.follow()
			self.assertEqual(response.status_code, 200)

			self.assertIn("Logged in as {username}".format(username=user.username), response.body.decode('utf-8'))

	def test_impersonate_as_user(self):
		users = list(UserProfile.objects.all().exclude(username=self.user.username))
		users.append(get_anonymous_user())

		for user in users:
			response = self.app.post('/hijack/{user_id}/'.format(user_id=user.id), user=user)
			self.assertRedirects(response, reverse('admin:login') + '?next=/hijack/{user_id}/'.format(user_id=user.id))

	def test_impersonate_wrong_url(self):
		user = UserProfile.objects.get(username='test')

		response = self.app.post('/hijack/{email}/'.format(email=user.email), user=self.user, expect_errors=True)
		self.assertEqual(response.status_code, 400)

		response = self.app.post('/hijack/{username}/'.format(username=user.username), user=self.user, expect_errors=True)
		self.assertEqual(response.status_code, 400)
