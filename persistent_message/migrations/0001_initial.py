# Generated by Django 2.1.4 on 2018-12-13 18:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('level', models.IntegerField(choices=[(20, 'Info'), (25, 'Success'), (30, 'Warning'), (40, 'Danger')], default=20)),
                ('begins', models.DateTimeField()),
                ('expires', models.DateTimeField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('modified_by', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.SlugField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='TagGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='tag',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='persistent_message.TagGroup'),
        ),
        migrations.AddField(
            model_name='message',
            name='tags',
            field=models.ManyToManyField(to='persistent_message.Tag'),
        ),
    ]
