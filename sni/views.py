
#
# Satoshi Nakamoto Institute (http://nakamotoinstitute.org)
# Copyright 2013 Satoshi Nakamoto Institute
# Licensed under GNU Affero GPL (https://github.com/pierrerochard/SNI-private/blob/master/LICENSE)
#

from sni import app, db, cache
from models import Post, Email, Doc, Author, Format, Category, BlogPost, Skeptic
from flask import render_template, json, url_for, redirect, request
from sqlalchemy import desc
from werkzeug.contrib.atom import AtomFeed
import re

from jinja2 import evalcontextfilter, Markup, escape


@app.errorhandler(404)
def internal_error(error):
    app.logger.error(str(request.remote_addr) + ', 404')
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(str(request.remote_addr) + ', 500')
    return render_template('500.html'), 500

@app.route("/", subdomain="satoshi")
def satoshi_index():
    app.logger.info(str(request.remote_addr) + ', SatoshiIndex')
    return render_template("satoshiindex.html")

@app.route('/')
def index():
    bp = BlogPost.query.order_by(desc(BlogPost.added)).first()
    app.logger.info(str(request.remote_addr) + ', Index')
    return render_template("index.html", bp=bp)

@app.route('/about/', methods = ["GET"])
def about():
    app.logger.info(str(request.remote_addr) + ', About')
    return render_template("about.html")

@app.route('/contact/', methods = ["GET"])
def contact():
    app.logger.info(str(request.remote_addr) + ', Contact')
    return render_template("contact.html")

@cache.cached(timeout=900)
@app.route('/emails/', subdomain="satoshi", methods = ["GET"])
@app.route('/emails/cryptography/', subdomain="satoshi", methods = ["GET"])
def emails():
    emails = Email.query.order_by(Email.date)
    app.logger.info(str(request.remote_addr) + ', Emails')
    return render_template("emails.html", emails=emails)

@cache.cached(timeout=900)
@app.route('/emails/cryptography/<int:emnum>/', subdomain="satoshi", methods = ["GET"])
def emailview(emnum):
    email = Email.query.filter_by(id=emnum).first()
    prev = Email.query.filter_by(id=emnum-1).first()
    next = Email.query.filter_by(id=emnum+1).first()
    if(email!=None):
        app.logger.info(str(request.remote_addr) + ', Emails, ' + str(emnum))
        return render_template("emailview.html", email=email, prev=prev, next=next)
    else:
        return redirect('emails')

@cache.cached(timeout=900)
@app.route('/posts/', subdomain="satoshi", methods = ["GET"])
def posts():
    posts = Post.query.order_by(Post.date).all()
    app.logger.info(str(request.remote_addr) + ', posts')
    return render_template("posts.html", posts=posts, source=None)

@cache.cached(timeout=900)
@app.route('/posts/<string:source>/', subdomain="satoshi", methods = ["GET"])
def forumposts(source):
    posts = Post.query.filter_by(source=source).order_by(Post.date).all()
    if(len(posts)!=0):
        app.logger.info(str(request.remote_addr) + ', posts, ' + source)
        return render_template("posts.html", posts=posts, source=source)
    else:
        return redirect(url_for('posts'))

@cache.cached(timeout=900)
@app.route('/posts/<string:source>/<int:postnum>/', subdomain="satoshi", methods=["GET"])
def postview(postnum,source):
    post = Post.query.filter_by(id=postnum, source=source).first()
    prev = Post.query.filter_by(id=postnum-1, source=source).first()
    next = Post.query.filter_by(id=postnum+1, source=source).first()
    if(post!=None):
        app.logger.info(str(request.remote_addr) + ', posts ,' + source + ', ' + str(postnum))
        return render_template("postview.html", post=post, prev=prev, next=next)
    else:
        return redirect('posts')

@cache.cached(timeout=900)
@app.route('/authors/', methods=["GET"])
def authors():
    authors = Author.query.order_by(Author.last).all()
    app.logger.info(str(request.remote_addr) + ', authors')
    return render_template("authors.html", authors=authors)

@cache.cached(timeout=900)
@app.route('/authors/<string:authslug>/', methods=["GET"])
def author(authslug):
    if (authslug=='satoshi-nakamoto'):
        return redirect(url_for('satoshi_index'))
    author = Author.query.filter_by(slug=authslug).first()
    mem = author.blogposts.all()
    lit = author.docs.all()
    app.logger.info(str(request.remote_addr) + ', authors, ' + authslug)
    return render_template("author.html", author=author, mem=mem, lit=lit)

@cache.cached(timeout=900)
@app.route('/literature/', methods=["GET"])
def literature():
    docs = Doc.query.order_by('id').all()
    formats = {}
    for doc in docs:
        formlist = []
        for format in doc.formats:
            formlist += [format.name]
        formats[doc.slug] = formlist
    app.logger.info(str(request.remote_addr) + ', literature')
    return render_template("literature.html", docs=docs, formats=formats)

@cache.cached(timeout=900)
@app.route('/literature/<string:slug>/', methods=["GET"])
def docinfo(slug):
    doc = Doc.query.filter_by(slug=slug).first()
    if(doc!=None):
        forms = []
        for form in doc.formats:
            if form.name == 'html':
                forms += ['html']
            if form.name == 'pdf':
                forms += ['pdf']
            if form.name == 'txt':
                forms += ['txt']
            if form.name == 'unavailable':
                forms += ['una']
        app.logger.info(str(request.remote_addr) + ', literature, ' + slug)
        return render_template("docinfo.html",doc=doc, forms=forms)
    else:
        return redirect('literature')

@cache.cached(timeout=900)
@app.route('/literature/<int:docid>/', methods=["GET"])
def docinfoid(docid):
    doc = Doc.query.filter_by(id=docid).first()
    if(doc!=None):
        forms = []
        for form in doc.formats:
            if form.name == 'html':
                forms += ['html']
            if form.name == 'pdf':
                forms += ['pdf']
            if form.name == 'txt':
                forms += ['txt']
            if form.name == 'unavailable':
                forms += ['una']
        app.logger.info(str(request.remote_addr) + ', literature, ' + str(docid))
        return render_template("docinfo.html",doc=doc, forms=forms)
    else:
        return redirect('literature')

@cache.cached(timeout=900)
@app.route('/literature/<string:slug>/<string:format>/', methods=["GET"])
def docview(slug, format):
    doc = Doc.query.filter_by(slug=slug).first()
    if(doc!=None):
        formats = []
        for form in doc.formats:
            formats += [form.name]
        if format in formats:
            if(format=='html'):
                return redirect(url_for('slugview', slug=slug))
            else:
                return redirect(url_for('static', filename='docs/%(x)s.%(y)s' % {"x": slug, "y": format}))
        else:
            return redirect(url_for('docinfo', slug=slug))
    else:
        return redirect('literature')

@cache.cached(timeout=900)
@app.route('/literature/<int:docid>/<string:format>/', methods=["GET"])
def docviewid(docid, format):
    doc = Doc.query.filter_by(id=docid).first()
    if(doc!=None):
        formats = []
        for form in doc.formats:
            formats += [form.name]
        slug = doc.slug
        if format in formats:
            if(format=='html'):
                return redirect(url_for('slugview', slug=slug))
            else:
                return redirect(url_for('static', filename='docs/%(x)s.%(y)s' % {"x": slug, "y": format}))
        else:
            return redirect(url_for('docinfo', slug=doc.slug))
    else:
        return redirect('literature')

@cache.cached(timeout=900)
@app.route('/<string:slug>/', methods=["GET"])
def slugview(slug):
    doc = Doc.query.filter_by(slug=slug).first()
    if(doc!=None):
        docid = doc.id
        formats = []
        for form in doc.formats:
            formats += [form.name]
        if('html' in formats):
            app.logger.info(str(request.remote_addr) + ', slugview, ' + slug)
            return render_template("%s.html" % slug, doc=doc)
        else:
            return redirect('literature')
    else:
        return redirect('literature')


@cache.cached(timeout=900)
@app.route('/mempool/', methods=["GET"])
def blog():
    bps = BlogPost.query.order_by(desc(BlogPost.added)).all()
    app.logger.info(str(request.remote_addr) + ', mempool')
    return render_template('blog.html', bps=bps)

@cache.cached(timeout=900)
@app.route('/mempool/<string:slug>/', methods=["GET"])
def blogpost(slug):
    # Redirect for new appcoin slug
    if slug == "appcoins-are-fraudulent":
        return redirect(url_for("blogpost", slug="appcoins-are-snake-oil"))
    bp = BlogPost.query.filter_by(slug=slug).order_by(desc(BlogPost.date)).first()
    if(bp != None):
        app.logger.info(str(request.remote_addr) + ', mempool, ' + slug)
        return render_template('%s.html' % slug, bp=bp)
    else:
        return redirect(url_for("blog"))

@cache.cached(timeout=900)
@app.route('/mempool/feed/')
def atomfeed():
    feed = AtomFeed('Mempool | Satoshi Nakamoto Institute',
                    feed_url=request.url, url=request.url_root)
    articles = BlogPost.query.order_by(desc(BlogPost.added)).all()
    for article in articles:
        articleurl = url_for('blogpost', slug=article.slug, _external=True)
        content = article.excerpt + "<br><br><a href='"+articleurl+"'>Read more...</a>"
        feed.add(article.title, unicode(content),
                 content_type='html',
                 author=article.author[0].first + ' ' + article.author[0].last,
                 url=articleurl,
                 updated=article.added,
                 published=article.date)
    app.logger.info(str(request.remote_addr) + ', atomfeed')
    return feed.get_response()

@cache.cached(timeout=900)
@app.route('/the-skeptics/')
def skeptics():
    skeptics = Skeptic.query.order_by(Skeptic.date).all()
    app.logger.info(str(request.remote_addr) + ', the-skeptics')
    return render_template('the-skeptics.html', skeptics=skeptics)

# Redirect old links
@cache.cached(timeout=900)
@app.route('/<string:url_slug>.<string:format>/')
def reroute(url_slug, format):
    doc=Doc.query.filter_by(slug=url_slug).first()
    if(doc!=None):
        return redirect(url_for("docview", slug=doc.slug, format=format))
    else:
        return redirect(url_for("index"))
