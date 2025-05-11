from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
import time
# Importar los modelos necesarios
from apps.base.models.support import (
    ARL, EPS, AccountType, AplicationStatus, BloodType, CivilStatus, 
    ContractType, DocType, Gender, HousingType, IndustryType, 
    InvoiceStatus, JobType, NoveltyType, PaymentMethod, PensionFound, 
    Periodicity, Priority, ProductType, RequestStatus, RetirementType, 
    ServiceType, SeveranceWithdawalType, TaskType, ThemeType, 
    TransactionType
)
from apps.third_party.models.third_party import ThirdPartyType
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = 'Carga datos iniciales de selección (tipos, estados, catálogos)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--level',
            type=str,
            choices=[
                'doc_types', 'transaction_types', 'account_types', 'periodicities',
                'genders', 'blood_types', 'contract_types', 'payment_methods',
                'civil_status', 'novelty_types', 'job_types', 'severance_types',
                'retirement_types', 'housing_types', 'third_party_types', 'eps',
                'pension_funds', 'arl', 'product_types', 'task_types', 'service_types',
                'invoice_status', 'priorities', 'industry_types', 'theme_types',
                'request_status', 'application_status', 'groups', 'permissions',
                'initial_users', 'all'
            ],
            default='all',
            help='Especificar el tipo de datos a cargar'
        )
        
        parser.add_argument(
            '--batch',
            type=int,
            default=100,
            help='Tamaño del lote para carga masiva'
        )

    def handle(self, *args, **options):
        level = options['level']
        batch_size = options['batch']
        
        start_time = time.time()
        self.stdout.write(self.style.MIGRATE_HEADING(f"Iniciando carga de datos de selección - Nivel: {level}"))
        
        try:
            with transaction.atomic():
                if level == 'doc_types' or level == 'all':
                    self.load_doc_types()
                
                if level == 'transaction_types' or level == 'all':
                    self.load_transaction_types()
                
                if level == 'account_types' or level == 'all':
                    self.load_account_types()
                
                if level == 'periodicities' or level == 'all':
                    self.load_periodicities()
                
                if level == 'genders' or level == 'all':
                    self.load_genders()
                
                if level == 'blood_types' or level == 'all':
                    self.load_blood_types()
                
                if level == 'contract_types' or level == 'all':
                    self.load_contract_types()
                
                if level == 'payment_methods' or level == 'all':
                    self.load_payment_methods()
                
                if level == 'civil_status' or level == 'all':
                    self.load_civil_status()
                
                if level == 'novelty_types' or level == 'all':
                    self.load_novelty_types()
                
                if level == 'job_types' or level == 'all':
                    self.load_job_types()
                
                if level == 'severance_types' or level == 'all':
                    self.load_severance_withdrawal_types()
                
                if level == 'retirement_types' or level == 'all':
                    self.load_retirement_types()
                
                if level == 'housing_types' or level == 'all':
                    self.load_housing_types()
                
                if level == 'third_party_types' or level == 'all':
                    self.load_third_party_types()
                
                if level == 'eps' or level == 'all':
                    self.load_eps()
                
                if level == 'pension_funds' or level == 'all':
                    self.load_pension_funds()
                
                if level == 'arl' or level == 'all':
                    self.load_arl()
                
                if level == 'product_types' or level == 'all':
                    self.load_product_types()
                
                if level == 'task_types' or level == 'all':
                    self.load_task_types()
                
                if level == 'service_types' or level == 'all':
                    self.load_service_types()
                
                if level == 'invoice_status' or level == 'all':
                    self.load_invoice_status()
                
                if level == 'priorities' or level == 'all':
                    self.load_priorities()
                
                if level == 'industry_types' or level == 'all':
                    self.load_industry_types()
                
                if level == 'theme_types' or level == 'all':
                    self.load_theme_types()
                
                if level == 'chart_types' or level == 'all':
                    self.load_chart_types()
                
                if level == 'request_status' or level == 'all':
                    self.load_request_status()
                
                if level == 'application_status' or level == 'all':
                    self.load_application_status()
                
                if level == 'groups' or level == 'all':
                    self.load_groups()
                
                if level == 'permissions' or level == 'all':
                    self.load_permissions()
                
                if level == 'initial_users' or level == 'all':
                    self.load_initial_users()
                
                if level == 'company' or level == 'all':
                    self.load_company()
                
                if level == 'tax_regime' or level == 'all':
                    self.load_tax_regime()
                
                if level == 'comercial_company_type' or level == 'all':
                    self.load_comercial_company_type()
                
                if level == 'fiscal_responsibility' or level == 'all':
                    self.load_fiscal_responsibility()
                
                if level == 'question_types' or level == 'all':
                    self.load_question_types()
                    
                
            elapsed_time = time.time() - start_time
            self.stdout.write(self.style.SUCCESS(f"✅ Carga de datos de selección completada en {elapsed_time:.2f} segundos"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error en la carga de datos de selección: {str(e)}"))
            raise CommandError(f"La carga de datos de selección falló: {str(e)}")

    def load_question_types(self):
        """Carga los tipos de preguntas"""
        self.stdout.write("Cargando tipos de preguntas...")
        
        try:
            question_types = [
                ('TEXT', 'Campo de texto simple'),
                ('TEXT_AREA', 'Campo de texto multilínea'),
                ('SINGLE_CHOICE', 'Selección única entre varias opciones'),
                ('MULTIPLE_CHOICE', 'Selección múltiple entre varias opciones'),
                ('RATING', 'Evaluación en escala'),
                ('DATE', 'Selector de fecha'),
                ('NUMBER', 'Campo numérico'),
                ('YES_NO', 'Pregunta de Sí/No'),
                ('HIERARCHY', 'Pregunta jerárquica')
            ]
            
            created_count = 0
            for name, description in question_types:
                from apps.surveys.models.surveymodel import QuestionType
                _, created = QuestionType.objects.get_or_create(
                    name=name,
                    defaults={'description': description}
                )
                if created:
                    created_count += 1
            
            self.stdout.write(self.style.SUCCESS(f"✅ Tipos de preguntas creados: {created_count} de {len(question_types)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los tipos de preguntas: {str(e)}'))
            raise

    def load_doc_types(self):
        """Carga los tipos de documento"""
        self.stdout.write("Cargando tipos de documento...")
        
        try:
            doc_types = [
                'Cédula de Ciudadanía',
                'Cédula de Extranjería',
                'Pasaporte',
                'Tarjeta de Identidad',
                'Número de Identificación Tributaria'
            ]
            for name in doc_types:
                DocType.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS("✅ Tipos de documento creados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los tipos de documento: {str(e)}'))
            raise

    def load_transaction_types(self):
        """Carga los tipos de transacción"""
        self.stdout.write("Cargando tipos de transacción...")
        
        try:
            transaction_types = [
                ('DB', 'DEBITO'),
                ('CR', 'CREDITO')
            ]
            for code, name in transaction_types:
                TransactionType.objects.get_or_create(
                    code=code,
                    defaults={'name': name}
                )
            self.stdout.write(self.style.SUCCESS("✅ Tipos de transacción creados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los tipos de transacción: {str(e)}'))
            raise

    def load_account_types(self):
        """Carga los tipos de cuenta"""
        self.stdout.write("Cargando tipos de cuenta...")
        
        try:
            account_types = [
                ('CC', 'Cuenta Corriente'),
                ('CA', 'Cuenta de Ahorros')
            ]
            for code, name in account_types:
                AccountType.objects.get_or_create(
                    code=code,
                    defaults={'name': name}
                )
            self.stdout.write(self.style.SUCCESS("✅ Tipos de cuenta creados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los tipos de cuenta: {str(e)}'))
            raise

    def load_periodicities(self):
        """Carga las periodicidades"""
        self.stdout.write("Cargando periodicidades...")
        
        try:
            periodicities = [
                ('D', 'Diario', 1, 0),
                ('S', 'Semanal', 7, 0),
                ('Q', 'Quincenal', 15, 0),
                ('M', 'Mensual', 30, 1),
                ('B', 'Bimestral', 60, 2),
                ('T', 'Trimestral', 90, 3),
                ('SM', 'Semestral', 180, 6),
                ('A', 'Anual', 365, 12)
            ]
            for code, name, days, months in periodicities:
                Periodicity.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'days': days,
                        'months': months
                    }
                )
            self.stdout.write(self.style.SUCCESS("✅ Periodicidades creadas"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar las periodicidades: {str(e)}'))
            raise

    def load_genders(self):
        """Carga los géneros"""
        self.stdout.write("Cargando géneros...")
        
        try:
            genres = ['Masculino', 'Femenino', 'Otro']
            for name in genres:
                Gender.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS("✅ Géneros creados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los géneros: {str(e)}'))
            raise

    def load_blood_types(self):
        """Carga los tipos de sangre"""
        self.stdout.write("Cargando tipos de sangre...")
        
        try:
            blood_types = [
                ('+', 'O'), ('-', 'O'),
                ('+', 'A'), ('-', 'A'),
                ('+', 'B'), ('-', 'B'),
                ('+', 'AB'), ('-', 'AB')
            ]
            for rh, abo in blood_types:
                BloodType.objects.get_or_create(rh=rh, abo=abo)
            self.stdout.write(self.style.SUCCESS("✅ Tipos de sangre creados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los tipos de sangre: {str(e)}'))
            raise

    def load_contract_types(self):
        """Carga los tipos de contrato"""
        self.stdout.write("Cargando tipos de contrato...")
        
        try:
            contract_types = [
                ('Término Indefinido', 'Contrato sin fecha de terminación establecida'),
                ('Término Fijo', 'Contrato con fecha de terminación establecida'),
                ('Obra Labor', 'Contrato por duración de una obra específica'),
                ('Aprendizaje', 'Contrato de formación para aprendices')
            ]
            for name, description in contract_types:
                ContractType.objects.get_or_create(
                    name=name,
                    defaults={'description': description}
                )
            self.stdout.write(self.style.SUCCESS("✅ Tipos de contrato creados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los tipos de contrato: {str(e)}'))
            raise

    def load_payment_methods(self):
        """Carga los métodos de pago"""
        self.stdout.write("Cargando métodos de pago...")
        
        try:
            payment_methods = [
                ('E001', 'Efectivo'),
                ('T002', 'Transferencia'),
                ('TC03', 'Tarjeta de Crédito'),
                ('TD04', 'Tarjeta de Débito')                    
            ]
            for code, name in payment_methods:
                PaymentMethod.objects.get_or_create(name=name, code=code)
            self.stdout.write(self.style.SUCCESS("✅ Métodos de pago creados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los métodos de pago: {str(e)}'))
            raise

    def load_civil_status(self):
        """Carga los estados civiles"""
        self.stdout.write("Cargando estados civiles...")
        
        try:
            civil_status = [
                ('S001', 'Soltero'),
                ('C002', 'Casado'),
                ('D003', 'Divorciado'),
                ('V004', 'Viudo'),
                ('U005', 'Unión Libre')
            ]
            for code, name in civil_status:
                CivilStatus.objects.get_or_create(name=name, code=code)
            self.stdout.write(self.style.SUCCESS("✅ Estados civiles creados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los estados civiles: {str(e)}'))
            raise

    def load_novelty_types(self):
        """Carga los tipos de novedad"""
        self.stdout.write("Cargando tipos de novedad...")
        
        try:
            novelty_types = [
                'Personal',
                'Cita Medica',
                'Dia Laboral',
                'Vacaciones',
                'Licencia por Calamidad',
                'Licencia por Maternidad',
                'Licencia por Paternidad',
                'Licencia por Luto',
                'Otros'
            ]
            for name in novelty_types:
                NoveltyType.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS("✅ Tipos de novedad creados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los tipos de novedad: {str(e)}'))
            raise

    def load_job_types(self):
        """Carga los tipos de trabajo"""
        self.stdout.write("Cargando tipos de trabajo...")
        
        try:
            job_types = [
                ('Tiempo Completo', 'Trabajo de tiempo completo (48 horas semanales)'),
                ('Medio Tiempo', 'Trabajo de medio tiempo (24 horas semanales)'),
                ('Freelance', 'Trabajo independiente por proyectos')
            ]
            for name, description in job_types:
                JobType.objects.get_or_create(
                    name=name,
                    defaults={'description': description}
                )
            self.stdout.write(self.style.SUCCESS("✅ Tipos de trabajo creados"))                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los tipos de trabajo: {str(e)}'))
            raise

    def load_severance_withdrawal_types(self):
        """Carga los tipos de retiro de cesantías"""
        self.stdout.write("Cargando tipos de retiro de cesantías...")
        
        try:
            severance_withdawal_types = [
                'Mejoramiento de Vivienda',
                'Estudios',
                'Compra de Vivienda',
                'Finalizacion de Contrato',
            ]            
            for name in severance_withdawal_types:
                SeveranceWithdawalType.objects.get_or_create(
                    name=name
                )
            self.stdout.write(self.style.SUCCESS("✅ Tipos de retiro de cesantías creados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los tipos de retiro de cesantías: {str(e)}'))
            raise

    def load_retirement_types(self):
        """Carga los tipos de retiro laboral"""
        self.stdout.write("Cargando tipos de retiro laboral...")
        
        try:
            retirement_types = [
                'Retiro Voluntario',
                'Termino de Contrato',
                'Pension',              
            ]
            for name in retirement_types:
                RetirementType.objects.get_or_create(
                    name=name
                )
            self.stdout.write(self.style.SUCCESS("✅ Tipos de retiro laboral creados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los tipos de retiro laboral: {str(e)}'))
            raise

    def load_housing_types(self):
        """Carga los tipos de vivienda"""
        self.stdout.write("Cargando tipos de vivienda...")
        
        try:
            housing_types = [
                ('Propia', 'Vivienda propia'),
                ('Alquilada', 'Vivienda alquilada'),
                ('Familiar', 'Vivienda familiar'),
                ('Cedida', 'Vivienda cedida'),
            ]
            for name, description in housing_types:
                HousingType.objects.get_or_create(
                    name=name,
                    defaults={'description': description}
                )
            self.stdout.write(self.style.SUCCESS("✅ Tipos de vivienda creados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los tipos de vivienda: {str(e)}'))
            raise

    def load_third_party_types(self):
        """Carga los tipos de terceros"""
        self.stdout.write("Cargando tipos de terceros...")
        
        try:
            third_party_types = [
                ('CLI', 'Cliente'),
                ('PRO', 'Proveedor'),
                ('EMP', 'Empleado'),
                ('ACC', 'Accionista'),
                ('ASO', 'Contratista'),
                ('OTR', 'Otro')
            ]
            for code, name in third_party_types:
                ThirdPartyType.objects.get_or_create(
                    code=code,
                    defaults={'name': name}
                )
            self.stdout.write(self.style.SUCCESS("✅ Tipos de terceros creados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los tipos de terceros: {str(e)}'))
            raise

    def load_eps(self):
        """Carga las EPS"""
        self.stdout.write("Cargando EPS...")
        
        try:
            entidades_eps = [
                (1, 'ALIANSALUD ENTIDAD PROMOTORA DE SALUD S.A.'),
                (2, 'ASOCIACIÓN INDÍGENA DEL CAUCA'),
                (3, 'ASOCIACION MUTUAL SER EMPRESA SOLIDARIA DE SALUD EPS'),
                (4, 'CAPITAL SALUD'),
                (5, 'COMFENALCO  VALLE  E.P.S.'),
                (6, 'COMPENSAR   E.P.S.'),
                (7, 'COOPERATIVA DE SALUD Y DESARROLLO INTEGRAL ZONA SUR ORIENTAL DE CARTAGENA'),
                (8, 'E.P.S.  FAMISANAR LTDA. '),
                (9, 'E.P.S.  SANITAS S.A.'),
                (10, 'EPS  CONVIDA'),
                (11, 'EPS SERVICIO OCCIDENTAL DE SALUD S.A.'),
                (12, 'EPS Y MEDICINA PREPAGADA SURAMERICANA S.A'),
                (13, 'FUNDACION SALUD MIA EPS'),
                (14, 'MALLAMAS'),
                (15, 'NUEVA EPS S.A.'),
                (16, 'SALUD TOTAL S.A.  E.P.S.'),
                (17, 'SALUDVIDA S.A. E.P.S'),
                (18, 'SAVIA SALUD EPS'),
            ]

            for code, name in entidades_eps:
                EPS.objects.get_or_create(code=code, defaults={'name': name})
            self.stdout.write(self.style.SUCCESS("✅ Datos de EPS cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de EPS: {str(e)}'))
            raise

    def load_pension_funds(self):
        """Carga los fondos de pensiones"""
        self.stdout.write("Cargando fondos de pensiones...")
        
        try:
            fondo_pension = [
                (1, 'PROTECCION SA'),
                (2, 'PORVENIR SA'),
                (3, 'COLFONDOS'),
                (4, 'COLPENSIONES'),
                (5, 'OLD MUTUAL SA'),
                (6, 'ASOCIACION COLOMBIANA DE AVIADORES CIVILES ACDAC'),
                (7, 'ECOPETROL'),
                (8, 'FONDO DE PRESTACIONES SOCIALES DEL MAGISTERIO'),
            ]

            for code, name in fondo_pension:
                PensionFound.objects.get_or_create(code=code, defaults={'name': name})
            self.stdout.write(self.style.SUCCESS("✅ Datos de fondos de pensiones cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de fondos de pensiones: {str(e)}'))
            raise

    def load_arl(self):
        """Carga las ARL"""
        self.stdout.write("Cargando ARL...")
        
        try:
            arl_object = [
                (1, 'ARL Sura'),
                (2, 'Seguros Positiva'),
                (3, 'Seguros Colpatria'),
                (4, 'ARL Colmena'),
                (5, 'Seguros Bolívar'),
                (6, 'ARL Alfa'),
                (7, 'ARL Aurora'),
                (8, 'ARL Liberty Seguros'),
                (9, 'ARL La Equidad'),
                (10, 'ARL Mapfre')
            ]

            for code, name in arl_object:
                ARL.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS("✅ Datos de ARL cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de ARL: {str(e)}'))
            raise

    def load_product_types(self):
        """Carga los tipos de productos"""
        self.stdout.write("Cargando tipos de productos...")
        
        try:
            pruduct_type = [
                'ingreso',
                'Salida',
                'Cambio de Departamento',
                'Cambio de Cargo',
                'Cambio de Jefe',
                'Cambio de Area',
                'Cambio de Departamento',
                'Cambio de Nivel',
            ]
            for name in pruduct_type:
                ProductType.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS("✅ Datos de tipos de productos cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de tipos de productos: {str(e)}'))
            raise

    def load_task_types(self):
        """Carga los tipos de tareas"""
        self.stdout.write("Cargando tipos de tareas...")
        
        try:
            task_type = [
                'Llamada',
                'Reunion',
                'Correo Electronico'
            ]
            for name in task_type:
                TaskType.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS("✅ Datos de tipos de tareas cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de tipos de tareas: {str(e)}'))
            raise

    def load_service_types(self):
        """Carga los tipos de servicios"""
        self.stdout.write("Cargando tipos de servicios...")
        
        try:
            product_type = [
                'Hardware',
                'Software',
                'Servicio',
                'Software Libre',
                'Componente',
                'Licencia',
            ]
            for name in product_type:
                ServiceType.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS("✅ Datos de tipos de servicios cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de tipos de servicios: {str(e)}'))
            raise

    def load_invoice_status(self):
        """Carga los estados de facturas"""
        self.stdout.write("Cargando estados de facturas...")
        
        try:
            invoice_status = [
                'Pendiente',
                'Pagada',
                'Anulada',
                'Enviada',
                'Recibida',
                'En Proceso',
                'Rechazada',
                'Revisada',
                'En Revision',
                'En Corte',
                'Entregada',
                'Aprobada',
                'Revisada por Gerente',
                'Rechazada por Gerente',
                'Aprobada por Gerente',
                'Enviada a Corte',
                'Entregada a Corte',
                'Aprobada a Corte',
                'Revisada a Corte',
                'Rechazada a Corte',
                'Enviada a Aprobacion',
                'Entregada a Aprobacion',
                'Aprobada a Aprobacion',
                'Revisada a Aprobacion',
            ]
            for name in invoice_status:
                InvoiceStatus.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS("✅ Datos de estados de facturas cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de estados de facturas: {str(e)}'))
            raise

    def load_priorities(self):
        """Carga las prioridades"""
        self.stdout.write("Cargando prioridades...")
        
        try:
            prioridad = [
                'Alta',
                'Media',
                'Baja',
            ]
            for name in prioridad:
                Priority.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS("✅ Datos de prioridades cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de prioridades: {str(e)}'))
            raise

    def load_industry_types(self):
        """Carga los tipos de industria"""
        self.stdout.write("Cargando tipos de industria...")
        
        try:
            industria = [
                'Agricultura',
                'Alimentos',
                'Construcción',
                'Comercio',
                'Servicios',
                'Transporte',
                'Informática',
                'Educación',
                'Salud',
                'Finanzas',
                'Manufactura',
                'Otros',
            ]
            for name in industria:
                IndustryType.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS("✅ Datos de tipos de industria cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de tipos de industria: {str(e)}'))
            raise

    def load_theme_types(self):
        """Carga los tipos de temas"""
        self.stdout.write("Cargando tipos de temas...")
        
        try:
            temas = [
                ('light', 'Claro'),
                ('dark', 'Oscuro'),
                ('system', 'Sistema'),
            ]
            for name, code in temas:
                ThemeType.objects.get_or_create(name=name, code=code)
            self.stdout.write(self.style.SUCCESS("✅ Datos de tipos de temas cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de tipos de temas: {str(e)}'))
            raise
    
    def load_chart_types(self):
        """Carga los tipos de gráficos"""
        self.stdout.write("Cargando tipos de gráficos...")
        try:
            from apps.dashboard.models.dashboard_models import ChartType
            CHART_TYPES = [
                ("Bar Chart","BAR_CHART","Gráfico de barras para comparaciones entre categorías."),
                ("Pie Chart","PIE_CHART","Gráfico circular para mostrar proporciones."),
                ("Line Chart","LINE_CHART","Gráfico de líneas que muestra tendencias."),
                ("Scatter Plot","SCATTER_PLOT","Gráfico de dispersión para analizar correlaciones."),
                ("Histogram","HISTOGRAM","Histograma para mostrar distribuciones de datos."),
                ("Area Chart","AREA_CHART","Gráfico de área con volumen bajo la línea."),
                ("Radar Chart","RADAR_CHART","Gráfico de radar para comparar múltiples variables."),
                ("Heatmap","HEATMAP","Mapa de calor que representa valores con colores."),
                ("Bubble Chart","BUBBLE_CHART","Gráfico de burbujas con dimensiones adicionales."),
                ("Candlestick Chart","CANDLESTICK_CHART","Gráfico de velas para análisis financiero."),
                ("Box Plot","BOX_PLOT","Gráfico de caja para distribuciones de datos."),
                ("Sankey Diagram","SANKEY_DIAGRAM","Diagrama Sankey que visualiza flujos."),
                ("Funnel Chart","FUNNEL_CHART","Gráfico de embudo para fases de un proceso."),
                ("Network Graph","NETWORK_GRAPH","Gráfico de red que muestra conexiones."),
                ("Donut Chart","DONUT_CHART","Gráfico de dona para proporciones."),
                ("Waterfall Chart","WATERFALL_CHART","Gráfico de cascada que muestra contribuciones."),
                ("Stacked Bar Chart","STACKED_BAR_CHART","Gráfico de barras apiladas para comparaciones."),
                ("Treemap","TREEMAP","Mapa jerárquico que muestra proporciones entre categorías."),
                ("Parallel Coordinates Plot","PARALLEL_COORDINATES_PLOT","Gráfico de coordenadas paralelas para múltiples dimensiones."),
                ("Chord Diagram","CHORD_DIAGRAM","Diagrama de acordes que muestra relaciones entre entidades."),
                ("Gauge Chart","GAUGE_CHART","Gráfico de indicadores para representar progreso."),
                ("Sunburst Chart","SUNBURST_CHART","Gráfico de explosión solar jerárquico."),
                ("Timeline","TIMELINE","Línea de tiempo para eventos secuenciales."),
                ("Violin Plot","VIOLIN_PLOT","Gráfico de violín que muestra distribución de datos."),
                ("Step Chart","STEP_CHART","Gráfico escalonado para datos discretos.")
            ]
            for name, code, description in CHART_TYPES:
                ChartType.objects.get_or_create(name=name, code=code, description=description)
            print('✅ Datos iniciales de Tipos de Gráficos cargados.')
        except Exception as e:
            print('❌ Error al cargar los datos iniciales:', e)


    def load_request_status(self):
        """Carga los estados de solicitud"""
        self.stdout.write("Cargando estados de solicitud...")
        
        try:
            status_solicitud = [
                ('RS001', 'Abierta'),
                ('RS002', 'En Proceso'),
                ('RS003', 'Cerrada'),
            ]
            for code, name in status_solicitud:
                RequestStatus.objects.get_or_create(code=code, name=name)
            self.stdout.write(self.style.SUCCESS("✅ Datos de estados de solicitud cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de estados de solicitud: {str(e)}'))
            raise

    def load_application_status(self):
        """Carga los estados de aplicación/trámite"""
        self.stdout.write("Cargando estados de aplicación/trámite...")
        
        try:
            estados_solicitud = [
                (1, 'Pre Aprobado'),
                (2, 'Aprobado'),
                (3, 'Re agendado'),
                (4, 'Cancelado'),
                (5, 'En proceso'),
                (6, 'Finalizado'),
            ]
            for code, name in estados_solicitud:
                AplicationStatus.objects.get_or_create(code=code, name=name)
            self.stdout.write(self.style.SUCCESS("✅ Datos de estados de aplicación/trámite cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de estados de aplicación/trámite: {str(e)}'))
            raise

    def load_groups(self):
        """Carga los grupos de usuarios"""
        self.stdout.write("Cargando grupos de usuarios...")
        
        try:
            grupos = [
                'Administrador',
                'Colaborador',
                'Gerente',
            ]
            for name in grupos:
                Group.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS("✅ Datos de grupos de usuarios cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de grupos de usuarios: {str(e)}'))
            raise

    def load_permissions(self):
        """Carga los permisos a los grupos"""
        self.stdout.write("Cargando permisos a los grupos...")
        
        try:
            # Agregar todos los permisos al grupo Administrador
            admin_group = Group.objects.get(name='Administrador')
            permisos = Permission.objects.all()
            admin_group.permissions.add(*permisos)
            self.stdout.write(self.style.SUCCESS("✅ Permisos asignados al grupo Administrador"))
            
            # Agregar permisos específicos al grupo Colaborador
            colaborador_group = Group.objects.get(name='Colaborador')
            colaborador_permissions = Permission.objects.filter(
                Q(codename__icontains='permiso') | Q(codename__icontains='vacaciones')
            )
            colaborador_group.permissions.add(*colaborador_permissions)
            self.stdout.write(self.style.SUCCESS("✅ Permisos asignados al grupo Colaborador"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los permisos a los grupos: {str(e)}'))
            raise

    def load_initial_users(self):
        """Carga los usuarios iniciales"""
        self.stdout.write("Cargando usuarios iniciales...")
        
        try:
            from apps.base.models.users import User
            
            # Crear o obtener el grupo "Administrador"
            admin_group, created_group = Group.objects.get_or_create(name='Administrador')
            if created_group:
                self.stdout.write(self.style.SUCCESS(f"Grupo creado: {admin_group.name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Grupo existente: {admin_group.name}"))
            
            # Crear usuarios iniciales
            usuarios = [
                ('Administrador', '123456'),
            ]
            
            for username, password in usuarios:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'is_superuser': True,
                        'is_staff': True,
                        'email': 'correo@example.com'
                    }
                )
                
                if created:
                    user.set_password(password)
                    user.save()
                    user.groups.add(admin_group)
                    self.stdout.write(self.style.SUCCESS(f"✅ Usuario {username} creado correctamente"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"✅ Usuario {username} ya existe"))
            
            self.stdout.write(self.style.SUCCESS("✅ Usuarios iniciales cargados correctamente"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los usuarios iniciales: {str(e)}'))
            raise
    
    def load_company(self):
        """Carga los datos de la empresa"""
        self.stdout.write("Cargando datos de la empresa...")
        
        try:
            from apps.base.models.company import Company
            company, created = Company.objects.get_or_create(
                name='Mi Empresa SAS',
                defaults={
                    'tax_id': '1234567890',
                    'address': 'Calle 123 # 45-67',
                    'phone': '1234567',
                    'email': 'micorreo@email.com',
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS("✅ Datos de la empresa creados"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Datos de la empresa ya existen"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de la empresa: {str(e)}'))
            raise

    def load_tax_regime(self):
        """Carga los regímenes tributarios"""
        self.stdout.write("Cargando regímenes tributarios...")
        
        try:
            from apps.base.models.company import TaxRegime
            tax_regimes = [
                ('RC','Régimen Comun'),
                ('RO', 'Régimen Ordinario'),
                ('RS', 'Régimen Simplificado'),
                ('RE', 'Régimen Especial'),
            ]
            for code, name in tax_regimes:
                TaxRegime.objects.get_or_create(code=code, name=name)
            self.stdout.write(self.style.SUCCESS("✅ Datos de regímenes tributarios cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de regímenes tributarios: {str(e)}'))
            raise
    
    def load_comercial_company_type(self):
        """Carga los tipos de empresa"""
        self.stdout.write("Cargando tipos de empresa...")
        
        try:
            from apps.base.models.company import ComercialCompanyType
            comercial_company_types = [
                ('SAS','Sociedad por Acciones Simplificada'),
                ('SA','Sociedad Anónima'),
                ('LTDA','Sociedad de Responsabilidad Limitada'),
                ('SC','Sociedad Colectiva'),
                ('SCS','Sociedad Comanditaria Simple'),
                ('SCA','Sociedad Comanditaria por Acciones'),
                ('SCP','Empresa Unipersonal'),
                ('SEM','Sociedad de Economía Mixta'),
                ('COOP','Cooperativa'),
                ('SE','Sociedad Extranjera'),
            ]
            for code, name in comercial_company_types:
                ComercialCompanyType.objects.get_or_create(code=code, name=name)
            self.stdout.write(self.style.SUCCESS("✅ Datos de tipos de empresa cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de tipos de empresa: {str(e)}'))
            raise
    
    def load_fiscal_responsibility(self):
        """Carga las responsabilidades fiscales"""
        self.stdout.write("Cargando responsabilidades fiscales...")
        
        try:
            from apps.base.models.company import FiscalResponsibility
            fiscal_responsibilities = [
                ('O-01','Aporte especial para la Administración de Justicia'),
                    ('O-02','Gravamen a los Movimientos Financieros'),
                    ('O-03','Impuesto al patrimonio'),
                    ('O-04','Impuesto de renta y complementario régimen especial'),
                    ('O-05','Impuesto de renta y complementario régimen ordinario'),
                    ('O-06','Ingresos y patrimonio'),
                    ('O-07','Retención en la fuente a título de renta'),
                    ('O-08','Retención timbre nacional'),
                    ('O-09','Retención en la fuente en el impuesto sobre las ventas'),
                    ('O-10','Usuario aduanero'),
                    ('O-11','Ventas régimen común'),
                    ('O-12','Ventas régimen simplificado'),
                    ('O-13','Gran contribuyente'),
                    ('O-14','Informante de exógena'),
                    ('O-15','Autorretenedor'),
                    ('O-16','Obligación a facturar por ingresos de bienes y/o servicios excluidos'),
                    ('O-17','Profesionales de compra y venta de divisas'),
                    ('O-18','Precios de transferencia'),
                    ('O-19','Productor de bienes y/o servicios exentos (incluye exportadores),'),
                    ('O-20','Obtención NIT Organismos Economía Solidaria DIAN'),
                    ('O-21','Declarar ingreso o salida del país de divisas o moneda legal colombiana'),
                    ('O-22','Obligado a cumplir deberes formales a nombre de terceros'),
                    ('O-23','Agente de retención en ventas'),
                    ('O-24','Declaración consolidada precios de transferencia'),
                    ('O-25','Declaración individual precios de transferencia'),
                    ('O-26','Declaración de contribución por contratos de obra pública o concesión'),
                    ('O-32','Impuesto Nacional al Consumo'),
                    ('O-33','Impuesto Nacional a la Gasolina y al ACPM'),
                    ('O-34','Régimen simplificado impuesto nacional consumo restaurantes y bares'),
                    ('O-35','Impuesto sobre la Renta para la Equidad CREE'),
                    ('O-36','Establecimiento Permanente'),
                    ('O-37','Obligado a Facturar Electrónicamente'),
                    ('O-38','Facturación Electrónica Voluntaria'),
                    ('O-39','Proveedor de Servicios Tecnológicos PST'),
                    ('O-40','Impuesto a la Riqueza'),
                    ('O-41','Declaración anual de activos en el exterior'),
                    ('O-42','Obligado a Llevar Contabilidad'),
                    ('O-43','Impuesto Nacional al Carbono'),
                    ('O-44','Régimen SIMPLE'),
                    ('O-47','Régimen Simple de Tributación - SIMPLE'),
                    ('O-48','Impuesto sobre las ventas - IVA'),
                    ('O-49','No responsable de IVA'),
                    ('O-50','Apoyo al deporte de alto rendimiento (Art. 97 Ley 2010 de 2019),'),
                    ('O-51','Obras por impuestos (Art. 800-1 E.T.)'),
                    ('O-52','Contribuyente del impuesto unificado bajo el régimen simple de tributación - SIMPLE'),
                    ('O-53','Impuesto Nacional al Consumo de Bolsas Plásticas'),
                    ('O-54','Facturador electrónico (Persona natural sin actividad económica),'),
                    ('O-55','Autorretenedor de rendimientos financieros'),
                    ('O-56','Impuesto a las bebidas azucaradas'),
                    ('O-57','Impuesto a los alimentos ultraprocesados'),
                    ('O-58','Impuesto a los plásticos de un solo uso')
            ]
            for code, name in fiscal_responsibilities:
                FiscalResponsibility.objects.get_or_create(code=code, name=name)
            self.stdout.write(self.style.SUCCESS("✅ Datos de responsabilidades fiscales cargados"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al cargar los datos de responsabilidades fiscales: {str(e)}'))
            raise