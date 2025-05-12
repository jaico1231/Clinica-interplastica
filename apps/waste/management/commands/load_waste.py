from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import time
from apps.waste.models.waste_model import WasteType

class Command(BaseCommand):
    help = 'Carga los datos iniciales para la gestión de residuos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--level',
            type=str,
            choices=[
                'waste_types', 'waste_managers', 'all'
            ],
            default='all',
            help='Especificar el tipo de datos a cargar'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la actualización de datos existentes',
        )

    def handle(self, *args, **options):
        level = options['level']
        force_update = options['force']
        
        start_time = time.time()
        self.stdout.write(self.style.MIGRATE_HEADING(f"Iniciando carga de datos de gestión de residuos - Nivel: {level}"))
        
        try:
            with transaction.atomic():
                if level == 'waste_types' or level == 'all':
                    self.load_waste_types(force_update)
                
                if level == 'waste_managers' or level == 'all':
                    self.load_waste_managers(force_update)
                
                elapsed_time = time.time() - start_time
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Carga de datos de gestión de residuos completada en {elapsed_time:.2f} segundos"
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error en la carga de datos de gestión de residuos: {str(e)}"))
            raise CommandError(f"La carga de datos de gestión de residuos falló: {str(e)}")

    def load_waste_types(self, force_update=False):
        """Carga los tipos de residuos predefinidos en el sistema"""
        self.stdout.write("Cargando tipos de residuos...")
        
        try:
            # Definición de tipos de residuos con sus propiedades
            waste_types = [
                # Residuos ordinarios
                {
                    'name': 'Residuos de comida',
                    'code': 'ORD-001',
                    'category': 'ORDINARY',
                    'description': 'Restos de comida no aprovechables',
                    'identification_color': 'Verde',
                    'requires_special_treatment': False,
                    'handling_instructions': 'Depositar en bolsas cerradas',
                    'storage_requirements': 'Mantener en recipientes cerrados para evitar olores',
                    'safety_measures': 'No requiere medidas especiales',
                    'legal_classification': 'Residuo sólido ordinario',
                },
                {
                    'name': 'Papel sanitario',
                    'code': 'ORD-002',
                    'category': 'ORDINARY',
                    'description': 'Papel higiénico, toallas de papel, servilletas usadas',
                    'identification_color': 'Verde',
                    'requires_special_treatment': False,
                    'handling_instructions': 'Depositar en bolsas cerradas',
                    'storage_requirements': 'Almacenar en contenedores cerrados',
                    'safety_measures': 'No requiere medidas especiales',
                    'legal_classification': 'Residuo sólido ordinario',
                },
                
                # Residuos reciclables
                {
                    'name': 'Papel y cartón',
                    'code': 'REC-001',
                    'category': 'RECYCLABLE',
                    'description': 'Papel de oficina, periódicos, revistas, cajas de cartón',
                    'identification_color': 'Gris',
                    'requires_special_treatment': False,
                    'handling_instructions': 'Separar por tipo (papel/cartón) y mantener seco',
                    'storage_requirements': 'Almacenar en lugar seco y protegido de la intemperie',
                    'safety_measures': 'No requiere medidas especiales',
                    'legal_classification': 'Residuo aprovechable',
                },
                {
                    'name': 'Plástico PET',
                    'code': 'REC-002',
                    'category': 'RECYCLABLE',
                    'description': 'Botellas de bebidas, envases PET',
                    'identification_color': 'Azul',
                    'requires_special_treatment': False,
                    'handling_instructions': 'Enjuagar antes de desechar, retirar etiquetas si es posible',
                    'storage_requirements': 'Compactar para reducir volumen',
                    'safety_measures': 'No requiere medidas especiales',
                    'legal_classification': 'Residuo aprovechable',
                },
                {
                    'name': 'Vidrio',
                    'code': 'REC-003',
                    'category': 'RECYCLABLE',
                    'description': 'Botellas, frascos y envases de vidrio',
                    'identification_color': 'Blanco',
                    'requires_special_treatment': False,
                    'handling_instructions': 'Enjuagar antes de desechar, separar por color si es posible',
                    'storage_requirements': 'Almacenar en contenedores resistentes para evitar roturas',
                    'safety_measures': 'Manipular con cuidado para evitar cortes',
                    'legal_classification': 'Residuo aprovechable',
                },
                {
                    'name': 'Metales',
                    'code': 'REC-004',
                    'category': 'RECYCLABLE',
                    'description': 'Latas de aluminio, chatarra metálica, envases metálicos',
                    'identification_color': 'Gris',
                    'requires_special_treatment': False,
                    'handling_instructions': 'Limpiar de restos de alimentos si es necesario',
                    'storage_requirements': 'Almacenar en contenedores resistentes',
                    'safety_measures': 'Manipular con cuidado para evitar cortes con bordes afilados',
                    'legal_classification': 'Residuo aprovechable',
                },
                
                # Residuos peligrosos
                {
                    'name': 'Baterías y pilas',
                    'code': 'HAZ-001',
                    'category': 'HAZARDOUS',
                    'description': 'Pilas alcalinas, baterías de litio, baterías recargables',
                    'identification_color': 'Rojo',
                    'requires_special_treatment': True,
                    'handling_instructions': 'No mezclar con otros residuos, depositar en contenedores específicos',
                    'storage_requirements': 'Almacenar en contenedores herméticos resistentes a la corrosión',
                    'safety_measures': 'Evitar contacto con la piel, no incinerar',
                    'legal_classification': 'Residuo peligroso - Y31',
                },
                {
                    'name': 'Residuos químicos',
                    'code': 'HAZ-002',
                    'category': 'HAZARDOUS',
                    'description': 'Solventes, ácidos, reactivos químicos',
                    'identification_color': 'Rojo',
                    'requires_special_treatment': True,
                    'handling_instructions': 'Mantener en envases originales cuando sea posible, etiquetar claramente',
                    'storage_requirements': 'Almacenar en área ventilada, sobre contención secundaria',
                    'safety_measures': 'Usar EPP adecuado: guantes, gafas, máscara si es necesario',
                    'legal_classification': 'Residuo peligroso - Y14, Y34, Y35',
                },
                {
                    'name': 'Residuos biológicos',
                    'code': 'HAZ-003',
                    'category': 'HAZARDOUS',
                    'description': 'Material con riesgo biológico o infeccioso',
                    'identification_color': 'Rojo',
                    'requires_special_treatment': True,
                    'handling_instructions': 'Depositar en bolsas rojas y contenedores rígidos para cortopunzantes',
                    'storage_requirements': 'Almacenar en área refrigerada si es necesario, acceso restringido',
                    'safety_measures': 'Usar EPP completo: guantes, bata, gafas, mascarilla',
                    'legal_classification': 'Residuo peligroso - Y1',
                },
                
                # Residuos especiales
                {
                    'name': 'Escombros',
                    'code': 'SPE-001',
                    'category': 'SPECIAL',
                    'description': 'Residuos de construcción y demolición',
                    'identification_color': 'Naranja',
                    'requires_special_treatment': True,
                    'handling_instructions': 'Separar materiales reciclables como metal o madera',
                    'storage_requirements': 'Almacenar en contenedores específicos o área designada',
                    'safety_measures': 'Usar guantes y protección respiratoria si hay polvo',
                    'legal_classification': 'Residuo especial - RCD',
                },
                {
                    'name': 'Muebles y enseres',
                    'code': 'SPE-002',
                    'category': 'SPECIAL',
                    'description': 'Muebles viejos, colchones, alfombras',
                    'identification_color': 'Naranja',
                    'requires_special_treatment': True,
                    'handling_instructions': 'Evaluar posibilidad de donación o reciclaje de componentes',
                    'storage_requirements': 'Almacenar protegido de la intemperie',
                    'safety_measures': 'Manipular con precaución por peso y volumen',
                    'legal_classification': 'Residuo voluminoso',
                },
                
                # Residuos biodegradables
                {
                    'name': 'Residuos de jardinería',
                    'code': 'BIO-001',
                    'category': 'BIODEGRADABLE',
                    'description': 'Recortes de césped, hojas, ramas pequeñas',
                    'identification_color': 'Marrón',
                    'requires_special_treatment': False,
                    'handling_instructions': 'Separar material leñoso de material verde',
                    'storage_requirements': 'Almacenar en contenedores ventilados',
                    'safety_measures': 'No requiere medidas especiales',
                    'legal_classification': 'Residuo biodegradable',
                },
                {
                    'name': 'Residuos orgánicos compostables',
                    'code': 'BIO-002',
                    'category': 'BIODEGRADABLE',
                    'description': 'Restos vegetales de cocina, cáscaras de frutas y verduras',
                    'identification_color': 'Marrón',
                    'requires_special_treatment': False,
                    'handling_instructions': 'Evitar incluir carnes, lácteos o grasas',
                    'storage_requirements': 'Almacenar en contenedores cerrados para evitar vectores',
                    'safety_measures': 'No requiere medidas especiales',
                    'legal_classification': 'Residuo orgánico aprovechable',
                },
                
                # Residuos electrónicos
                {
                    'name': 'Equipos informáticos',
                    'code': 'ELE-001',
                    'category': 'ELECTRONIC',
                    'description': 'Computadores, impresoras, monitores, periféricos',
                    'identification_color': 'Gris',
                    'requires_special_treatment': True,
                    'handling_instructions': 'Mantener intactos, retirar baterías si es posible',
                    'storage_requirements': 'Almacenar en lugar seco, protegido de la intemperie',
                    'safety_measures': 'Manipular con cuidado para evitar roturas de pantallas',
                    'legal_classification': 'Residuo de aparatos eléctricos y electrónicos (RAEE)',
                },
                {
                    'name': 'Pequeños electrodomésticos',
                    'code': 'ELE-002',
                    'category': 'ELECTRONIC',
                    'description': 'Teléfonos, calculadoras, pequeños aparatos electrónicos',
                    'identification_color': 'Gris',
                    'requires_special_treatment': True,
                    'handling_instructions': 'Retirar baterías antes de desechar',
                    'storage_requirements': 'Almacenar en contenedores específicos',
                    'safety_measures': 'Evitar golpes que puedan liberar componentes peligrosos',
                    'legal_classification': 'Residuo de aparatos eléctricos y electrónicos (RAEE)',
                },
            ]
            
            created_count = 0
            updated_count = 0
            
            for waste_type_data in waste_types:
                waste_type, created = WasteType.objects.get_or_create(
                    code=waste_type_data['code'],
                    defaults=waste_type_data
                )
                
                # Si se requiere actualización forzada y el registro ya existía
                if not created and force_update:
                    for key, value in waste_type_data.items():
                        setattr(waste_type, key, value)
                    waste_type.save()
                    updated_count += 1
                    self.stdout.write(f"  Actualizado: {waste_type.name} ({waste_type.code})")
                elif created:
                    created_count += 1
                    self.stdout.write(f"  Creado: {waste_type.name} ({waste_type.code})")
            
            self.stdout.write(self.style.SUCCESS(
                f"✅ Tipos de residuos creados: {created_count}, actualizados: {updated_count}"
            ))
            
            return created_count, updated_count
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los tipos de residuos: {str(e)}'))
            raise

    def load_waste_managers(self, force_update=False):
        """Carga los gestores de residuos predefinidos en el sistema"""
        self.stdout.write("Cargando gestores de residuos...")
        
        try:
            from apps.waste.models.waste_model import WasteManager
            
            # Definición de gestores de residuos con sus propiedades
            waste_managers = [
                {
                    'name': 'EcoGestión Ambiental',
                    'tax_id': '900123456-7',
                    'address': 'Calle 25 # 45-67, Zona Industrial',
                    'city': 'Medellín',
                    'phone': '604-1234567',
                    'email': 'contacto@ecogestion.com',
                    'website': 'https://www.ecogestion.com',
                    'environmental_license': 'RES-2023-0123',
                    'license_date': '2023-01-15',
                    'license_expiry_date': '2028-01-14',
                    'contact_person': 'María Rodríguez',
                    'contact_phone': '312-345-6789',
                    'services_offered': 'Gestión integral de residuos peligrosos, tratamiento de RAEE, incineración controlada',
                },
                {
                    'name': 'Reciclajes del Valle',
                    'tax_id': '901987654-3',
                    'address': 'Avenida Industrial 78-90',
                    'city': 'Cali',
                    'phone': '602-9876543',
                    'email': 'info@reciclajesvalle.com',
                    'website': 'https://www.reciclajesvalle.com',
                    'environmental_license': 'RES-2022-4567',
                    'license_date': '2022-06-10',
                    'license_expiry_date': '2027-06-09',
                    'contact_person': 'Carlos Gómez',
                    'contact_phone': '315-678-9012',
                    'services_offered': 'Reciclaje de papel, cartón, plástico, vidrio y metales. Compra de material reciclable.',
                },
                {
                    'name': 'BioResiduos Colombia',
                    'tax_id': '902345678-9',
                    'address': 'Carrera 15 # 123-45',
                    'city': 'Bogotá',
                    'phone': '601-3456789',
                    'email': 'contacto@bioresiduos.co',
                    'website': 'https://www.bioresiduos.co',
                    'environmental_license': 'RES-2021-7890',
                    'license_date': '2021-11-20',
                    'license_expiry_date': '2026-11-19',
                    'contact_person': 'Laura Martínez',
                    'contact_phone': '310-123-4567',
                    'services_offered': 'Gestión de residuos orgánicos, compostaje industrial, biodigestión, producción de abonos orgánicos.',
                },
                {
                    'name': 'RAEE Soluciones',
                    'tax_id': '903456789-0',
                    'address': 'Calle 67 # 12-34',
                    'city': 'Bogotá',
                    'phone': '601-5678901',
                    'email': 'info@raeesoluciones.com',
                    'website': 'https://www.raeesoluciones.com',
                    'environmental_license': 'RES-2022-1357',
                    'license_date': '2022-03-05',
                    'license_expiry_date': '2027-03-04',
                    'contact_person': 'Pedro Sánchez',
                    'contact_phone': '317-890-1234',
                    'services_offered': 'Gestión de residuos electrónicos, desarme de equipos, recuperación de materiales valiosos, destrucción segura de datos.',
                },
                {
                    'name': 'Escombros y RCD Gestión',
                    'tax_id': '904567890-1',
                    'address': 'Km 5 Vía Oriental',
                    'city': 'Medellín',
                    'phone': '604-6789012',
                    'email': 'operaciones@escombrosgestion.com',
                    'website': None,
                    'environmental_license': 'RES-2020-9876',
                    'license_date': '2020-09-15',
                    'license_expiry_date': '2025-09-14',
                    'contact_person': 'Jorge Ramírez',
                    'contact_phone': '320-234-5678',
                    'services_offered': 'Gestión y disposición de residuos de construcción y demolición, trituración y aprovechamiento de escombros.',
                }
            ]
            
            created_count = 0
            updated_count = 0
            
            for manager_data in waste_managers:
                # Convertir fechas de string a objetos date si es necesario
                if 'license_date' in manager_data and isinstance(manager_data['license_date'], str):
                    from datetime import datetime
                    manager_data['license_date'] = datetime.strptime(manager_data['license_date'], '%Y-%m-%d').date()
                
                if 'license_expiry_date' in manager_data and isinstance(manager_data['license_expiry_date'], str):
                    from datetime import datetime
                    manager_data['license_expiry_date'] = datetime.strptime(manager_data['license_expiry_date'], '%Y-%m-%d').date()
                
                manager, created = WasteManager.objects.get_or_create(
                    tax_id=manager_data['tax_id'],
                    defaults=manager_data
                )
                
                # Si se requiere actualización forzada y el registro ya existía
                if not created and force_update:
                    for key, value in manager_data.items():
                        setattr(manager, key, value)
                    manager.save()
                    updated_count += 1
                    self.stdout.write(f"  Actualizado: {manager.name} ({manager.tax_id})")
                elif created:
                    created_count += 1
                    self.stdout.write(f"  Creado: {manager.name} ({manager.tax_id})")
            
            self.stdout.write(self.style.SUCCESS(
                f"✅ Gestores de residuos creados: {created_count}, actualizados: {updated_count}"
            ))
            
            return created_count, updated_count
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los gestores de residuos: {str(e)}'))
            raise