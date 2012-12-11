# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Add field to allow searching for redirects
        db.add_column('wiki_document', 'is_redirect', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True))

        # Update existing records
        docs = orm.Document.objects.all()
        for doc in docs:
        	if doc.redirect_url():
        		doc.is_redirect = 1
        		doc.save()

    def backwards(self, orm):

    	# Remove added field
        db.delete_column('wiki_document', 'is_redirect')


    models = {
    	'wiki.document': {
            'Meta': {'unique_together': "(('parent', 'locale'), ('slug', 'locale'))", 'object_name': 'Document'},
            'category': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'current_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'current_for+'", 'null': 'True', 'to': "orm['wiki.Revision']"}),
            'defer_rendering': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'html': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_localizable': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'is_template': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'is_redirect': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'last_rendered_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'locale': ('sumo.models.LocaleField', [], {'default': "'en-US'", 'max_length': '7', 'db_index': 'True'}),
            'mindtouch_page_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'translations'", 'null': 'True', 'to': "orm['wiki.Document']"}),
            'parent_topic': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['wiki.Document']"}),
            'related_documents': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['wiki.Document']", 'through': "orm['wiki.RelatedDocument']", 'symmetrical': 'False'}),
            'render_scheduled_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'render_started_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'rendered_errors': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'rendered_html': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        }
    }

    complete_apps = ['wiki']