from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from django import forms

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.comments.views.comments import post_comment
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.sites.models import Site

from addons.main.models import Addon, Category, Screenshot, Versioning

from tagging.models import Tag
from tagging import utils
from datetime import datetime

def stripTags(s):
    ''' Strips HTML tags.
        Taken from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/440481
    '''
    intag = [False]

    def chk(c):
        if intag[0]:
            intag[0] = (c != '>')
            return False
        elif c == '<':
            intag[0] = True
            return False
        return True

    return ''.join(c for c in s if chk(c))

def get_first_thumb_link(addon):
    return addon.screenshot_set.all()[0].url

def tag_linkify(tags):
    tag_string = ''
    for t in tags:
        tag_string += '<a href="/tag/'+str(t.name)+'">'+str(t.name)+'</a> '
    return tag_string

### VIEWS ###

def login_user(request):
    import django.contrib.auth.views
    if not request.user.is_authenticated():
        return django.contrib.auth.views.login(request, template_name='registration/login.html')
    else:
        return HttpResponseRedirect("/")

class RegisterForm(forms.Form):
        """
        Standard registration form
        """
        login = forms.CharField(min_length=3, max_length=30)
        password1 = forms.CharField(min_length=6)
        password2 = forms.CharField(min_length=6)
        email = forms.EmailField()
        def clean(self):
                # check if passwords match
                if 'password2' in self.cleaned_data and 'password1' in self.cleaned_data and self.cleaned_data['password2'] != self.cleaned_data['password1'] :
                        raise forms.ValidationError(_("Passwords do not match."))
                # check if login is free
                try:
                        User.objects.get(username=self.cleaned_data['login'])
                except:
                        pass
                else:
                        raise forms.ValidationError(_("Login already taken"))
                # check if email isn't used already
                try:
                        User.objects.get(email=self.cleaned_data['email'])
                except:
                        pass
                else:
                        raise forms.ValidationError(_("Email already taken"))

                return self.cleaned_data

def register(request):
        """
        User registration
        """
        if not request.user.is_authenticated():
            form =  RegisterForm()
            if request.POST:
                    data = request.POST.copy()
                    data['login'] = stripTags(data['login'])
                    data['email'] = stripTags(data['email'])

                    form = RegisterForm(data)

                    if form.is_valid():
                            data = form.cleaned_data
                            try:
                                    user = User.objects.create_user(data['login'], data['email'], data['password1'])
                            except Exception:
                                    data['reply'] = ''
                                    return render_to_response(
                                            'registration/registration.html',
                                            {'form': form, 'error': True})
                            else:
                                    user.save()
                                    user = authenticate(username=data['login'], password=data['password1'])
                                    if user is not None:
                                            login(request, user)
                                    return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Registration compleated. You have been logged in succesfuly.'), 'redirect_to': "/"})
                    else:
                            data['reply'] = ''
                            # newforms are bad... ;)
                            if '__all__' in form.errors:
                                    if str(form.errors['__all__']).find(_("Login already taken")) != -1:
                                            form.errors['login'] = [_("Login already taken"),]
                                    if str(form.errors['__all__']).find(_("Email already taken")) != -1:
                                            form.errors['email'] = [_("Email already taken"),]
                                    if str(form.errors['__all__']).find(_("Passwords do not match.")) != -1:
                                            form.errors['password1'] = [_("Passwords do not match."),]
                            return render_to_response(
                                    'registration/registration.html',
                                    {'form': form, 'error': True})

            return render_to_response(
                    'registration/registration.html',
                    {'form': form})
        else:
            return render_to_response('main/msg.html', {'user': request.user, 'msg': _('You are already logged in.'), 'redirect_to': "/"})

def index(request):
    if request.user.is_authenticated():
        #User should have that after authorisation
        #request.user.user_permissions.add('User')
        pass
    #latest_addons = Addon.objects.all().order_by('-pub_date')[:5]
    recomended_addons = Addon.objects.all().order_by('-rating')[:4]
    categories = Category.objects.all()
    tags = Tag.objects.usage_for_model(Addon, counts=True)
    tag_cloud = utils.calculate_cloud(tags, steps=5, distribution=utils.LOGARITHMIC)
    return render_to_response('main/index.html', {'tag_cloud': tag_cloud, 'recomended_addons': recomended_addons, 'categories': categories, 'user': request.user, 'site_name': Site.objects.get_current().name})

@login_required(redirect_field_name='/addon/my/')
def my_addons(request, sortby = ''):
    page_name = _('Your addons')
    if sortby == 'sortby/ratings':
        sortby = '-rating'
    elif sortby == 'sortby/pubdate':
        sortby = '-pub_date'
    elif sortby == 'sortby/modification':
        sortby = '-modified'
    elif sortby == 'sortby/downloads':
        sortby = '-n_downloads'
    else:
        sortby = '-id'
    if request.user.is_authenticated():
        addons = request.user.addon_set.all().order_by(sortby)
        paginator = Paginator(addons, 25)

        # Make sure page request is an int. If not, deliver first page.
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        # If page request (9999) is out of range, deliver last page of results.
        try:
            addons = paginator.page(page)
        except (EmptyPage, InvalidPage):
            addons = paginator.page(paginator.num_pages)
        return render_to_response('main/my_addons.html', {'addons': addons, 'user': request.user, 'site_name': Site.objects.get_current().name, 'page_name': page_name})
    else:
        return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Oops! Something went wrong.'), 'redirect_to': "/"})

class AddAddonForm(forms.ModelForm):
    #tags = forms.CharField(required=False, max_length=255, default=' trest')
    class Meta:
        # Nazwa modelu
        model = Addon
        fields = ('category', 'name', 'description')

@login_required(redirect_field_name='/addon/add')
def add_addon(request):
    if request.user.is_authenticated():
        if request.POST:
            data = request.POST.copy()
            data['name'] = stripTags(data['name'])
            data['description'] = stripTags(data['description'])
            data['pub_date'] = datetime.now()
            data['n_comments'] = 0
            data['n_downloads'] = 0
            data['modified'] = datetime.now()
            data['rating'] = 0
            data['tags'] = data['name']+' '+stripTags(data['tags'])
            form = AddAddonForm(data)
            if form.is_valid():
                # zapisanie komentarza do bazy
                data = form.save(commit=False)
                data.author = request.user
                data.rating = 0
                data.save()
                #Tag.objects.update_tags(data, data['tags'])
                return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Congratulations! Your addon was added successfuly.'), 'redirect_to': "/addon/"+str(data.id)})
        else:
            page_name = _("Add new addon")
            form = AddAddonForm()
            return render_to_response(
                    'main/form.html',
                    {'form':form, 'user': request.user, 'site_name': Site.objects.get_current().name, 'page_name': page_name})
    else:
        return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Oops! Something went wrong.'), 'redirect_to': "/"})

@login_required(redirect_field_name='/login/')
def edit_addon(request, id):
    try:
        id = int(id)
    except:
        return render_to_response('main/msg.html', {'user': request.user, 'msg': _('ID is not a integer.'), 'redirect_to': "/"})

    if request.user.is_authenticated():
        addon = get_object_or_404(Addon, pk=id)
        if request.user.id != addon.author.id:
            return render_to_response('main/msg.html', {'user': request.user, 'msg': _('It\'s not your addon.'), 'redirect_to': "/"})
        form = AddAddonForm(instance=addon)
        if request.POST:
            data = request.POST.copy()
            data['name'] = stripTags(data['name'])
            data['description'] = stripTags(data['description'])
            data['modified'] = datetime.now()
            form = AddAddonForm(data)
            if form.is_valid():
                # save edited info to DB
                data = form.save(commit=False)
                data.author = request.user
                data.id = addon.id
                data.pub_date = addon.pub_date
                data.n_comments = addon.n_comments
                data.n_downloads = addon.n_downloads
                data.rating = addon.rating
                data.save()
                Tag.objects.update_tags(data, request.POST['tags'])
                return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Congratulations! Your addon was edited successfuly.'), 'redirect_to': "/addon/"+str(data.id) })
        else:
            page_name = _("Edit addon")
            return render_to_response(
                    'main/form.html',
                    {'form':form, 'user': request.user, 'site_name': Site.objects.get_current().name, 'page_name': page_name})
    else:
        return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Oops! Something went wrong.'), 'redirect_to': "/"})

class AddScreenshotForm(forms.ModelForm):
    class Meta:
        # Model name
        model = Screenshot
        fields = ('description', 'screenshot')

@login_required(redirect_field_name='/login/')
def add_screenshot(request, id):
    try:
        id = int(id)
    except:
        return render_to_response('main/msg.html', {'user': request.user, 'msg': _('ID is not a integer.'), 'redirect_to': "/"})

    if request.user.is_authenticated():
        addon = get_object_or_404(Addon, pk=id)
        if request.user.id != addon.author.id:
            return render_to_response('main/msg.html', {'user': request.user, 'msg': _('It is not your addon.'), 'redirect_to': "/"})
        if request.POST and request.FILES:
            data = request.POST.copy()
            data['description'] = stripTags(data['description'])
            form = AddScreenshotForm(data, request.FILES)
            if form.is_valid():
                data = form.save(commit=False)
                data.addon = addon
                data.save()
                addon.modified = datetime.now()
                addon.save()
                return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Congratulations! Your screenshot was added successfuly.'), 'redirect_to': "/"})
            else:
                return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Oops! Something is invalid.'), 'redirect_to': "/"})
        else:
            page_name = _('Add new screenshot')
            form = AddScreenshotForm()
            return render_to_response(
                    'main/multipart_form.html',
                    {'form': form, 'user': request.user, 'site_name': Site.objects.get_current().name, 'page_name': page_name})
    else:
        return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Oops! Something went wrong.'), 'redirect_to': "/"})

class AddVersioningForm(forms.ModelForm):
    class Meta:
        model = Versioning
        fields = ('version', 'codename', 'description', 'file')

    def clean_file(self):
        from django.template.defaultfilters import filesizeformat

        self.MAX_UPLOAD_SIZE = 5242880
        content = self.cleaned_data['file']
        content_type = content.content_type
        #print content_type
        if content_type == 'application/zip' or content_type == 'application/x-compressed-tar' or content_type == 'application/gzip':
            if content._size > self.MAX_UPLOAD_SIZE:
                raise forms.ValidationError(_('Please keep filesize under %s. Current filesize %s') % (filesizeformat(self.MAX_UPLOAD_SIZE), filesizeformat(content._size)))
        else:
            raise forms.ValidationError(_('File type is not supported'))
        return content

@login_required(redirect_field_name='/login/')
def add_version(request, id):
    try:
        id = int(id)
    except:
        return render_to_response('main/msg.html', {'user': request.user, 'msg': _('ID is not a integer.'), 'redirect_to': "/"})

    if request.user.is_authenticated():
        addon = get_object_or_404(Addon, pk=id)
        if request.user.id != addon.author.id:
            return render_to_response('main/msg.html', {'user': request.user, 'msg': _('It is not your addon.'), 'redirect_to': "/"})
        if request.POST and request.FILES:
            data = request.POST.copy()
            data['version'] = stripTags(data['version'])
            data['codename'] = stripTags(data['codename'])
            data['description'] = stripTags(data['description'])
            form = AddVersioningForm(data, request.FILES)
            if form.is_valid():
                data = form.save(commit=False)
                data.addon = addon
                data.pub_date = datetime.now()
                addon.modified = datetime.now()
                addon.save()
                data.save()
                return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Congratulations! New version info about addon was added successfuly.'), 'redirect_to': "/addon/"+str(addon.id)})
            else:
                return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Oops! Something is invalid. Propably your addon file is too big or excension is invalid. Maximum allowed size is 5MB (extensions: zip and tar.gz).'), 'redirect_to': "/addon/"+str(addon.id)})
        else:
            page_name = _('Add new version')
            form = AddVersioningForm()
            return render_to_response(
                    'main/multipart_form.html',
                    {'form': form, 'user': request.user, 'site_name': Site.objects.get_current().name, 'page_name':page_name})
    else:
        return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Oops! Something went wrong.'), 'redirect_to': "/"})

@login_required(redirect_field_name='/login/')
def delete_screenshot(request, addon_id, screenshot_id):
    try:
        addon_id = int(addon_id)
        screenshot_id = int(screenshot_id)
    except:
        return render_to_response('main/msg.html', {'user': request.user, 'msg': _('ID is not a integer.'), 'redirect_to': "/"})

    if request.user.is_authenticated():
        addon = get_object_or_404(Addon, pk=addon_id)
        screenshot = get_object_or_404(Screenshot, pk=screenshot_id)
        if request.user.id != addon.author.id:
            return render_to_response('main/msg.html', {'user': request.user, 'msg': _('It is not your addon.'), 'redirect_to': "/"})

        screenshot.delete()
        return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Screenshot deleted successfuly.'), 'redirect_to': "/addon/"+str(addon.id)})

@login_required(redirect_field_name='/login/')
def delete_version(request, addon_id, version_id):
    try:
        addon_id = int(addon_id)
        version_id = int(version_id)
    except:
        return render_to_response('main/msg.html', {'user': request.user, 'msg': _('ID is not a integer.'), 'redirect_to': "/"})

    if request.user.is_authenticated():
        addon = get_object_or_404(Addon, pk=addon_id)
        version = get_object_or_404(Versioning, pk=version_id)
        if request.user.id != addon.author.id:
            return render_to_response('main/msg.html', {'user': request.user, 'msg': _('It is not your addon.'), 'redirect_to': "/"})

        version.delete()
        return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Version info deleted successfuly.'), 'redirect_to': "/addon/"+str(addon.id)})

def show_addon(request, id):
    addon = get_object_or_404(Addon, pk=id)
    is_author = False
    if request.user.is_authenticated():
        if request.user.id == addon.author.id:
            is_author = True
    screenshots = addon.screenshot_set.all()
    versions = addon.versioning_set.all().order_by('-pub_date')
    tags = tag_linkify(Tag.objects.get_for_object(addon))
    return render_to_response('main/show_addon.html',
        {'addon': addon, 'screenshots': screenshots, 'is_author': is_author, 'versions': versions, 'tags': tags, 'user': request.user, 'site_name': Site.objects.get_current().name})

def download_addon(request, id, version_id):
    addon = get_object_or_404(Addon, pk=id)
    version = Versioning.objects.get(id=version_id)
    addon.n_downloads = addon.n_downloads+1
    addon.save()
    return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Wait 2 seconds to download your file.'), 'redirect_to': version.file.url})

def show_category(request, id, sortby = ''):
    cat = get_object_or_404(Category, pk=id)
    page_name = _('Show addons for category: %s') % cat.name
    if sortby == 'sortby/ratings':
        sortby = '-rating'
    elif sortby == 'sortby/pubdate':
        sortby = '-pub_date'
    elif sortby == 'sortby/modification':
        sortby = '-modified'
    elif sortby == 'sortby/downloads':
        sortby = '-n_downloads'
    else:
        sortby = '-id'
    addons = cat.addon_set.all().order_by(sortby)
    #tags = tag_linkify(Tag.objects.get_for_object(addon))
    paginator = Paginator(addons, 25)

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        addons = paginator.page(page)
    except (EmptyPage, InvalidPage):
        addons = paginator.page(paginator.num_pages)

    return render_to_response('main/show_category.html', {'category': cat, 'addons':  addons, 'user': request.user, 'site_name': Site.objects.get_current().name, 'page_name': page_name})

@login_required(redirect_field_name='/login/')
def comment_post_wrapper(request):
    # Clean the request to prevent form spoofing
    if request.user.is_authenticated():
        if not (request.user.get_full_name() == request.POST['name'] or \
               request.user.email == request.POST['email']):
            return HttpResponse("You registered user...trying to spoof a form...eh?")
        return post_comment(request)
    return HttpResponse("You anonymous cheater...trying to spoof a form?")

@login_required(redirect_field_name='/login/')
def comment_posted(request, data):
    return render_to_response('main/msg.html', {'user': request.user, 'msg': _('Thank you for your comment!'), 'redirect_to': "/"})
