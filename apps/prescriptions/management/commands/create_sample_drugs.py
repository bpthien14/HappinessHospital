"""
Management command để tạo dữ liệu thuốc mẫu
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.prescriptions.models import DrugCategory, Drug

User = get_user_model()

class Command(BaseCommand):
    help = 'Tạo dữ liệu thuốc mẫu cho hệ thống'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Bắt đầu tạo dữ liệu thuốc mẫu...')
        
        # Get or create admin user for created_by field
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(username='admin').first()
        
        # Create drug categories
        categories_data = [
            {'code': 'ANTIBIOTICS', 'name': 'Kháng sinh', 'description': 'Thuốc kháng sinh điều trị nhiễm khuẩn'},
            {'code': 'ANALGESICS', 'name': 'Giảm đau', 'description': 'Thuốc giảm đau, hạ sốt'},
            {'code': 'CARDIOVASCULAR', 'name': 'Tim mạch', 'description': 'Thuốc điều trị bệnh tim mạch'},
            {'code': 'DIGESTIVE', 'name': 'Tiêu hóa', 'description': 'Thuốc điều trị tiêu hóa'},
            {'code': 'RESPIRATORY', 'name': 'Hô hấp', 'description': 'Thuốc điều trị hô hấp'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = DrugCategory.objects.get_or_create(
                code=cat_data['code'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description']
                }
            )
            categories[cat_data['code']] = category
            if created:
                self.stdout.write(f'✅ Tạo nhóm thuốc: {category.name}')
            else:
                self.stdout.write(f'⚠️ Nhóm thuốc đã tồn tại: {category.name}')
        
        # Create sample drugs
        drugs_data = [
            {
                'code': 'AMOX500',
                'name': 'Amoxicillin 500mg',
                'generic_name': 'Amoxicillin',
                'brand_name': 'Amoxil',
                'category': 'ANTIBIOTICS',
                'dosage_form': 'CAPSULE',
                'strength': '500mg',
                'unit': 'CAPSULE',
                'indication': 'Điều trị nhiễm khuẩn đường hô hấp, tiết niệu, da và mô mềm',
                'contraindication': 'Dị ứng với penicillin',
                'side_effects': 'Buồn nôn, tiêu chảy, phát ban',
                'dosage_adult': '500mg x 3 lần/ngày',
                'dosage_child': '25-45mg/kg/ngày chia 3 lần',
                'unit_price': 3000,
                'insurance_price': 2400,
                'current_stock': 500,
                'manufacturer': 'Công ty dược phẩm ABC',
                'country_of_origin': 'Việt Nam'
            },
            {
                'code': 'PARA500',
                'name': 'Paracetamol 500mg',
                'generic_name': 'Paracetamol',
                'brand_name': 'Tylenol',
                'category': 'ANALGESICS',
                'dosage_form': 'TABLET',
                'strength': '500mg',
                'unit': 'TABLET',
                'indication': 'Giảm đau, hạ sốt',
                'contraindication': 'Suy gan nặng',
                'side_effects': 'Hiếm khi có phản ứng dị ứng',
                'dosage_adult': '500-1000mg x 4 lần/ngày',
                'dosage_child': '10-15mg/kg x 4-6 lần/ngày',
                'unit_price': 500,
                'insurance_price': 400,
                'current_stock': 1000,
                'manufacturer': 'Dược phẩm XYZ',
                'country_of_origin': 'Việt Nam'
            },
            {
                'code': 'AMLOD5',
                'name': 'Amlodipine 5mg',
                'generic_name': 'Amlodipine besylate',
                'brand_name': 'Norvasc',
                'category': 'CARDIOVASCULAR',
                'dosage_form': 'TABLET',
                'strength': '5mg',
                'unit': 'TABLET',
                'indication': 'Điều trị tăng huyết áp, đau thắt ngực',
                'contraindication': 'Dị ứng với amlodipine',
                'side_effects': 'Phù mắt cá chân, đau đầu, mệt mỏi',
                'dosage_adult': '5-10mg x 1 lần/ngày',
                'dosage_child': 'Chưa có khuyến cáo',
                'unit_price': 8000,
                'insurance_price': 6400,
                'current_stock': 300,
                'manufacturer': 'Pfizer',
                'country_of_origin': 'Mỹ'
            },
            {
                'code': 'ESOME20',
                'name': 'Esomeprazole 20mg',
                'generic_name': 'Esomeprazole',
                'brand_name': 'Nexium',
                'category': 'DIGESTIVE',
                'dosage_form': 'CAPSULE',
                'strength': '20mg',
                'unit': 'CAPSULE',
                'indication': 'Điều trị loét dạ dày, trào ngược dạ dày thực quản',
                'contraindication': 'Dị ứng với esomeprazole',
                'side_effects': 'Đau đầu, buồn nôn, tiêu chảy',
                'dosage_adult': '20-40mg x 1 lần/ngày',
                'dosage_child': 'Theo cân nặng',
                'unit_price': 15000,
                'insurance_price': 12000,
                'current_stock': 200,
                'manufacturer': 'AstraZeneca',
                'country_of_origin': 'Thụy Điển'
            },
            {
                'code': 'SALBU2',
                'name': 'Salbutamol 2mg',
                'generic_name': 'Salbutamol',
                'brand_name': 'Ventolin',
                'category': 'RESPIRATORY',
                'dosage_form': 'TABLET',
                'strength': '2mg',
                'unit': 'TABLET',
                'indication': 'Điều trị hen suyễn, COPD',
                'contraindication': 'Dị ứng với salbutamol',
                'side_effects': 'Run tay, đánh trống ngực, đau đầu',
                'dosage_adult': '2-4mg x 3-4 lần/ngày',
                'dosage_child': '0.1-0.2mg/kg x 3 lần/ngày',
                'unit_price': 2000,
                'insurance_price': 1600,
                'current_stock': 400,
                'manufacturer': 'GSK',
                'country_of_origin': 'Anh'
            },
            {
                'code': 'CIPRO500',
                'name': 'Ciprofloxacin 500mg',
                'generic_name': 'Ciprofloxacin',
                'brand_name': 'Cipro',
                'category': 'ANTIBIOTICS',
                'dosage_form': 'TABLET',
                'strength': '500mg',
                'unit': 'TABLET',
                'indication': 'Điều trị nhiễm khuẩn đường tiết niệu, tiêu hóa',
                'contraindication': 'Trẻ em dưới 18 tuổi, phụ nữ có thai',
                'side_effects': 'Buồn nôn, tiêu chảy, đau đầu',
                'dosage_adult': '250-750mg x 2 lần/ngày',
                'dosage_child': 'Chống chỉ định',
                'unit_price': 5000,
                'insurance_price': 4000,
                'current_stock': 250,
                'manufacturer': 'Bayer',
                'country_of_origin': 'Đức'
            },
            {
                'code': 'IBU400',
                'name': 'Ibuprofen 400mg',
                'generic_name': 'Ibuprofen',
                'brand_name': 'Advil',
                'category': 'ANALGESICS',
                'dosage_form': 'TABLET',
                'strength': '400mg',
                'unit': 'TABLET',
                'indication': 'Giảm đau, kháng viêm, hạ sốt',
                'contraindication': 'Loét dạ dày, suy thận nặng',
                'side_effects': 'Đau dạ dày, buồn nôn, chóng mặt',
                'dosage_adult': '400mg x 3 lần/ngày',
                'dosage_child': '20-30mg/kg/ngày chia 3-4 lần',
                'unit_price': 2500,
                'insurance_price': 2000,
                'current_stock': 600,
                'manufacturer': 'Johnson & Johnson',
                'country_of_origin': 'Mỹ'
            },
            {
                'code': 'METF500',
                'name': 'Metformin 500mg',
                'generic_name': 'Metformin hydrochloride',
                'brand_name': 'Glucophage',
                'category': 'CARDIOVASCULAR',
                'dosage_form': 'TABLET',
                'strength': '500mg',
                'unit': 'TABLET',
                'indication': 'Điều trị tiểu đường type 2',
                'contraindication': 'Suy thận, suy gan nặng',
                'side_effects': 'Buồn nôn, tiêu chảy, đau bụng',
                'dosage_adult': '500mg x 2-3 lần/ngày',
                'dosage_child': 'Từ 10 tuổi trở lên',
                'unit_price': 1500,
                'insurance_price': 1200,
                'current_stock': 800,
                'manufacturer': 'Merck',
                'country_of_origin': 'Pháp'
            },
            {
                'code': 'RANIT150',
                'name': 'Ranitidine 150mg',
                'generic_name': 'Ranitidine',
                'brand_name': 'Zantac',
                'category': 'DIGESTIVE',
                'dosage_form': 'TABLET',
                'strength': '150mg',
                'unit': 'TABLET',
                'indication': 'Điều trị loét dạ dày, trào ngược',
                'contraindication': 'Dị ứng với ranitidine',
                'side_effects': 'Đau đầu, táo bón, chóng mặt',
                'dosage_adult': '150mg x 2 lần/ngày',
                'dosage_child': '2-4mg/kg x 2 lần/ngày',
                'unit_price': 3000,
                'insurance_price': 2400,
                'current_stock': 350,
                'manufacturer': 'GSK',
                'country_of_origin': 'Anh'
            },
            {
                'code': 'PRED5',
                'name': 'Prednisolone 5mg',
                'generic_name': 'Prednisolone',
                'brand_name': 'Deltacortril',
                'category': 'RESPIRATORY',
                'dosage_form': 'TABLET',
                'strength': '5mg',
                'unit': 'TABLET',
                'indication': 'Kháng viêm, ức chế miễn dịch, điều trị hen suyễn',
                'contraindication': 'Nhiễm trùng nấm hệ thống',
                'side_effects': 'Tăng cân, loãng xương, tăng đường huyết',
                'dosage_adult': '5-60mg/ngày tùy bệnh',
                'dosage_child': '0.5-2mg/kg/ngày',
                'unit_price': 1000,
                'insurance_price': 800,
                'current_stock': 450,
                'manufacturer': 'Pfizer',
                'country_of_origin': 'Mỹ'
            }
        ]
        
        for drug_data in drugs_data:
            category = categories[drug_data.pop('category')]
            
            drug, created = Drug.objects.get_or_create(
                code=drug_data['code'],
                defaults={
                    **drug_data,
                    'category': category,
                    'created_by': admin_user
                }
            )
            
            if created:
                self.stdout.write(f'✅ Tạo thuốc: {drug.name}')
            else:
                self.stdout.write(f'⚠️ Thuốc đã tồn tại: {drug.name}')
        
        self.stdout.write('🎉 Hoàn thành tạo dữ liệu thuốc mẫu!')
        self.stdout.write(f'📊 Tổng kết:')
        self.stdout.write(f'   - Nhóm thuốc: {DrugCategory.objects.count()}')
        self.stdout.write(f'   - Thuốc: {Drug.objects.count()}')
