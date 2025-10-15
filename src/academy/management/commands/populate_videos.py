from django.core.management.base import BaseCommand
from academy.models import Video


class Command(BaseCommand):
    help = 'Populate the database with sample videos with multi-language content'

    def handle(self, *args, **options):
        # Sample videos with content in multiple languages
        sample_videos = [
            {
                'tag': 'Programming',
                'video_minutes': 480,  # 8 hours
                'video_seconds': 0,
                'title': 'Angular Basics',  # Default fallback title
                'description': 'Introductory course for Angular and framework basics',  # Default fallback
                'title_persian': 'مبانی برنامه‌نویسی Angular',
                'description_persian': 'دوره مقدماتی Angular و اصول فریمورک',
                'title_arabic': 'أساسيات Angular',
                'description_arabic': 'دورة تمهيدية لإطار العمل Angular والأساسيات',
                'title_english': 'Basics of Angular',
                'description_english': 'Introductory course for Angular and framework basics',
                'title_turkish': 'Angular Temelleri',
                'description_turkish': 'Angular framework ve temel bilgiler için giriş kursu',
            },
            {
                'tag': 'Programming',
                'video_minutes': 720,  # 12 hours
                'video_seconds': 0,
                'title': 'React.js Fundamentals',
                'description': 'Learn the fundamentals of React.js and modern web development',
                'title_persian': 'اصول React.js',
                'description_persian': 'یادگیری اصول React.js و توسعه وب مدرن',
                'title_arabic': 'أساسيات React.js',
                'description_arabic': 'تعلم أساسيات React.js وتطوير الويب الحديث',
                'title_english': 'React.js Fundamentals',
                'description_english': 'Learn the fundamentals of React.js and modern web development',
                'title_turkish': 'React.js Temelleri',
                'description_turkish': 'React.js temellerini ve modern web geliştirmeyi öğrenin',
            },
            {
                'tag': 'Marketing',
                'video_minutes': 360,  # 6 hours
                'video_seconds': 0,
                'title': 'Digital Marketing Strategy',
                'description': 'Master digital marketing strategies and social media campaigns',
                'title_persian': 'استراتژی بازاریابی دیجیتال',
                'description_persian': 'تسلط بر استراتژی‌های بازاریابی دیجیتال و کمپین‌های رسانه‌های اجتماعی',
                'title_arabic': 'استراتيجية التسويق الرقمي',
                'description_arabic': 'إتقان استراتيجيات التسويق الرقمي وحملات وسائل التواصل الاجتماعي',
                'title_english': 'Digital Marketing Strategy',
                'description_english': 'Master digital marketing strategies and social media campaigns',
                'title_turkish': 'Dijital Pazarlama Stratejisi',
                'description_turkish': 'Dijital pazarlama stratejilerinde ve sosyal medya kampanyalarında uzmanlaşın',
            },
            {
                'tag': 'Programming',
                'video_minutes': 630,  # 10.5 hours = 630 minutes
                'video_seconds': 0,
                'title': 'Python for Beginners',
                'description': 'Complete guide to Python programming for beginners',
                'title_persian': 'پایتون برای مبتدیان',
                'description_persian': 'راهنمای کامل برنامه‌نویسی پایتون برای مبتدیان',
                'title_arabic': 'Python للمبتدئين',
                'description_arabic': 'دليل شامل لبرمجة Python للمبتدئين',
                'title_english': 'Python for Beginners',
                'description_english': 'Complete guide to Python programming for beginners',
                'title_turkish': 'Yeni Başlayanlar için Python',
                'description_turkish': 'Yeni başlayanlar için eksiksiz Python programlama rehberi',
            },
            {
                'tag': 'Data Science',
                'video_minutes': 435,  # 7.25 hours = 435 minutes
                'video_seconds': 0,
                'title': 'Data Analysis with Pandas',
                'description': 'Learn data analysis and manipulation using Python Pandas',
                'title_persian': 'تحلیل داده با Pandas',
                'description_persian': 'یادگیری تجزیه و تحلیل و دستکاری داده‌ها با استفاده از Pandas پایتون',
                'title_arabic': 'تحليل البيانات باستخدام Pandas',
                'description_arabic': 'تعلم تحليل البيانات ومعالجتها باستخدام Python Pandas',
                'title_english': 'Data Analysis with Pandas',
                'description_english': 'Learn data analysis and manipulation using Python Pandas',
                'title_turkish': 'Pandas ile Veri Analizi',
                'description_turkish': 'Python Pandas kullanarak veri analizi ve manipülasyonu öğrenin',
            }
        ]

        created_count = 0
        updated_count = 0
        
        for video_data in sample_videos:
            # Try to find existing video by title
            try:
                video = Video.objects.get(title=video_data['title'])
                # Update existing video with multi-language content
                for field, value in video_data.items():
                    setattr(video, field, value)
                video.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated existing video: {video.title}')
                )
            except Video.DoesNotExist:
                # Create new video with multi-language content
                video = Video.objects.create(**video_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created new video: {video.title}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {created_count} new videos and updated {updated_count} existing videos'
            )
        )