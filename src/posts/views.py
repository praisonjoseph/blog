from urllib.parse import quote_plus
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
# Create your views here.
from posts.models import Post
from posts.forms import PostForm
#from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from comments.forms import CommentForm
from comments.models import Comment
from django.contrib.contenttypes.models import ContentType


def post_create(request):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    # if not request.user.is_authenticated():
    #     raise Http404
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.user = request.user
        instance.save()
        messages.success(request, "Successfully Created")
        #return HttpResponseRedirect(instance.get_absolute_url())
        return redirect(instance)
    # else:
    #     messages.error(request, "Not Successfully Created")
    context = {
        "form": form
    }
    #import pdb; pdb.set_trace()
    return render(request,"post_form.html", context)


def post_detail(request, slug=None):
    # instance = Post.objects.get(id=16)
    instance = get_object_or_404(Post,slug=slug)
    if instance.draft or instance.publish > timezone.now().date():
        if not request.user.is_staff or not request.user.is_superuser:
            raise Http404
    initial_data = {
        "content_type": instance.get_content_type,
        "object_id": instance.id
    }
    form = CommentForm(request.POST or None, initial=initial_data)
    if form.is_valid():
        c_type = form.cleaned_data.get("content_type")
        content_type = ContentType.objects.get(model=c_type)
        obj_id = form.cleaned_data.get("object_id")
        content_data = form.cleaned_data.get("content")
        # print(content_type)
        new_comment, created = Comment.objects.get_or_create(
                            user = request.user,
                            content_type = content_type,
                            object_id = obj_id,
                            content = content_data
        )
        
    comments = instance.comments
    share_string = quote_plus(instance.content)
    context = {"instance": instance,
                "share_string": share_string,
                "comments": comments,
                "comment_form": form
                }

    return render(request,"post_detail.html", context)
def post_list(request):
    today = timezone.now().date()
    queryset_list = Post.objects.active()#.order_by("-timestamp")
    #print(settings.AUTH_USER_MODEL)
    if request.user.is_staff or request.user.is_superuser:
        queryset_list = Post.objects.all()
    query = request.GET.get("q")
    if query:
        queryset_list = queryset_list.filter(
        Q(title__icontains = query) |
        Q(content__icontains = query) |
        Q(user__first_name__icontains = query) |
        Q(user__last_name__icontains = query)).distinct()

    paginator = Paginator(queryset_list, 5) # Show 25 contacts per page
    page_request_var = "page"
    page = request.GET.get(page_request_var)
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        queryset = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        queryset = paginator.page(paginator.num_pages)
    #import pdb; pdb.set_trace()
    context = {"title": "List",
            "object_list": queryset,
            "today": today,
            "page_request_var": page_request_var
            }
    #import pdb; pdb.set_trace()
    return render(request,"post_list.html", context)

def post_update(request, slug=None):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    instance = get_object_or_404(Post,slug=slug)
    form = PostForm(request.POST or None, request.FILES or None, instance=instance)
    # import pdb; pdb.set_trace()
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        messages.success(request, "Saved")
        return HttpResponseRedirect(instance.get_absolute_url())
    context = {"title": instance.title,
                "instance": instance,
                "form": form}
    return render(request,"post_form.html", context)
def post_delete(request, slug=None):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    instance = get_object_or_404(Post,slug=slug)
    instance.delete()
    messages.success(request, "Successfully Deleted")
    return redirect("posts:list")
