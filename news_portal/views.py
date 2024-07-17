# Импортируем класс, который говорит нам о том,
# что в этом представлении мы будем выводить список объектов из БД
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.core.mail import send_mail, EmailMultiAlternatives # объект письма с HTML
from django.template.loader import render_to_string # функция для рендера HTML в строку
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, TemplateView
from django.shortcuts import render
from .models import Post, Comment, Category, Mail, PostCategory, UserSubcribes, User
from .filters import PostFilter
from .forms import PostForm, PstForm
from django.shortcuts import reverse, render, redirect
from datetime import datetime
from pprint import pprint

class ProtectedView(LoginRequiredMixin,TemplateView):
    template_name = 'flatpages/authorization.html'

class PostsList(ListView): #класс для показа общего списка всепх публикаций
    # Указываем модель, объекты которой мы будем выводить
    model = Post
    # Поле, которое будет использоваться для сортировки объектов
    # ordering = 'create_time'
    # Указываем имя шаблона, в котором будут все инструкции о том,
    # как именно пользователю должны быть показаны наши объекты
    template_name = 'flatpages/news.html'
    # Это имя списка, в котором будут лежать все объекты.
    # Его надо указать, чтобы обратиться к списку объектов в html-шаблоне.
    context_object_name = 'post'
    paginate_by = 10

    def form(self): # метод для присвоения формы, используемой при подписке на категории новостей
        form = PostForm()
        return form

    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        user=User.objects.get(pk=self.request.user.pk) # текущий авторизованный пользователь
        context['form'] = self.form()
        return context

    def post(self, request, *args, **kwargs):
        a=0
        spisok=[]
        form = PstForm(request)
        if request.method == "POST":
            form=PstForm(request.POST)
            if form.is_valid():
            # for i in form.fields['category'].choices:
                for i in form.cleaned_data['category']:
                    UserSubcribes.objects.create(subcribe_id=self.request.user.pk, category_id=i.pk)
                return render(request,'flatpages/messages.html',{'list':spisok})

    # def post(self):
    #     form = PostForm(self.request)
    #     if self.request.method=='POST':
    #         form=PostForm(request.POST)
    #         user=self.request.user
    #         for i in form.cleaned_data['category']:
    #             UserSubcribes.objects.create(subcriber=user.pk, category_id=i.pk)
    #     return render(self.request, 'flatpages/messages.html')









class PostDetail(DetailView): # детальная информация конкретного поста
    model = Post
    template_name = 'flatpages/post.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs): # модернизация контекста для отображения комментариев
                                                # на отдельной странице поста
        context=super().get_context_data(**kwargs)
        context['comm'] = Comment.objects.filter(post_id=self.kwargs['pk'])
        form=PostForm(initial={'title': self.object.title,
                               'content': self.object.content,
                               'create_time': self.object.create_time,
                               'author': self.object.author,
                               'postType': self.object.postType,
                               'category': PostCategory.objects.filter(post_id=self.kwargs['pk']) }
                               )
        form.fields['author'].disabled = True
        form.fields['title'].disabled = True
        form.fields['content'].disabled = True
        form.fields['create_time'].disabled = True
        form.fields['postType'].disabled = True
        form.fields['category'].disabled = True
        context['form'] = form
        context['id']=self.object.pk # переменная контекста, передающая id поста
        return context

class PostFilterView(ListView): # класс для отображения фильтра поста на отдельной HTML странице 'search.html'
    model = Post
    template_name = 'flatpages/search.html'
    context_object_name = 'post'
    paginate_by =3

    def get_queryset(self):
        queryset=super().get_queryset()
        self.filter = PostFilter(self.request.GET,queryset)
        return self.filter.qs

    def get_context_data(self,  **kwargs): #добавление в контекст фильтра
        context=super().get_context_data(**kwargs)
        context['filter']=self.filter
        return context

@login_required
def create_post(request): # функция для создания и добавления новой публикации
    form=PostForm()
    form.fields['create_time'].disabled = True
    if request.method=='POST':
        form=PostForm(request.POST)
        if form.is_valid():
            post=Post.objects.create(content=form.cleaned_data.get('content'),
                                     author=form.cleaned_data.get('author'),
                                     title=form.cleaned_data.get('title'),
                                     postType=form.cleaned_data.get('postType')
                                     )
            for i in form.cleaned_data['category']:
                PostCategory.objects.create(category_id=i.pk, post_id=post.pk)
            recepient_list=[]
            # for i in UserSubcribes.objects.filter(category=post.category):
            #     if i.subcribe.email not in recepient_list: # подписчик может быть подписан на несколько категорий
            #                         # в то же время пост может относиться к нескольким категориям одновременно.
            #                         # Поэтому, чтобы на одну и ту же статью не было повторных сообщенгий пользователю
            #                         # и вводится данное условие
            #         recepient_list.append(i.subcribe.email)
            # subcribers=Category.objects.filter(category=post.category)
            # send_mail(subject='New',
            #           message=f'New post {post.title} has been',
            #           from_email='sportactive.SK@yandex.ru')
            return render(request, 'flatpages/messages.html', {'state':'Новая публикация добавлена успешно!','list':recepient_list})
    return render(request, 'flatpages/edit.html', {'form':form, 'button':'Опубликовать'})

@login_required
def edit_post(request, pk): # функция для редактирования названия и содержания поста
    post = Post.objects.get(pk=pk)
    form=PostForm(initial={'create_time':post.create_time,
                           'author':post.author,
                           'postType':post.postType,
                           'title': post.title,
                           'content': post.content,
                           'category': PostCategory.objects.filter(post_id=post.pk)
                           })
    form.fields['postType'].disabled = True
    form.fields['author'].disabled = True
    form.fields['create_time'].disabled = True

    # recepient_list = []
    recepient_list=request.user.is_authenticated
    # for i in PostCategory.objects.filter(post_id=post.pk):
    #     for j in UserSubcribes.objects.filter(category_id=i.category_id):
    #     # if i.subcribe.email not in recepient_list:  # подписчик может быть подписан на несколько категорий
    #         # в то же время пост может относиться к нескольким категориям одновременно.
    #         # Поэтому, чтобы на одну и ту же статью не было повторных сообщенгий пользователю
    #         # и вводится данное условие
    #         recepient_list.append(j.subcribe.email)

    if request.method=='POST':
        form=PostForm(request.POST, post)
        form.fields['postType'].required = False
        form.fields['author'].required = False
        form.fields['create_time'].required = False
        try:
            if form.is_valid():
                Post.objects.filter(pk=pk).update(**{'author':post.author,
                                                     'postType':post.postType,
                                                     'create_time':post.create_time,
                                                     'title':form.cleaned_data['title'],
                                                     'content':form.cleaned_data['content']})
                return render(request, 'flatpages/messages.html', {'state': 'Изменения успешно сохранены.'})
        except TypeError:
            return render(request, 'flatpages/messages.html', {'state':'Возникла ошибка! Возможно причина в превышении лимита названия поста, попавшего в БД не через форму'})
    return render(request, 'flatpages/edit.html', {'form':form, 'button':'Сохранить изменения', 'list':recepient_list})

def delete_post(request, pk):
    post = Post.objects.get(pk=pk)
    if request.method=='POST':
        post.delete()
        return render(request, 'flatpages/messages.html', {'state': 'Пост успешно удален'})
    return render(request, 'flatpages/del_post.html',{'post':post})

class MailView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'flatpages/mail.html', {})

    def post(self, request, *args, **kwargs):
        mail = Mail(client=request.POST['client_name'],
                                   # date=datetime.strptime(request.POST['date'],''),
                                   message=request.POST['message'])
        mail.save()

        # отправка письма
        # send_mail(subject=f'{mail.client} ',
        #           message=mail.message, # сообщение с кратким описанием проблемы
        #           from_email='sportactive.SK@yandex.ru', # почта, с которой осуществляется отправка,
        #           recipient_list=['sportactive.SK@yandex.ru','rfa-kstu@yandex.ru'] # список полуяателей
        # )

        # преоьразование HTML в текст
        html_content =render_to_string('flatpages/send_html_mail.html', {'mail':mail})
        msg=EmailMultiAlternatives(subject=f'{mail.client} ',
                                   body=mail.message,
                                   from_email='sportactive.SK@yandex.ru',
                                   to=[f'{request.POST['email']}'])
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
        return render(request, 'flatpages/messages.html', {})




# Неиспользуемые классы ниже
class CommListView(ListView):  # класс для отобрпажения
    model = Comment
    template_name = 'flatpages/comm.html'
    context_object_name = 'cmts'