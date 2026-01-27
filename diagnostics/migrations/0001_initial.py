from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DiagnosticLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('level', models.CharField(max_length=10)),
                ('logger_name', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('request_path', models.CharField(blank=True, max_length=2048, null=True)),
                ('request_method', models.CharField(blank=True, max_length=10, null=True)),
                ('response_status', models.PositiveIntegerField(blank=True, null=True)),
                ('duration_ms', models.PositiveIntegerField(blank=True, null=True)),
                ('external_service', models.CharField(blank=True, max_length=255, null=True)),
                ('details', models.JSONField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
