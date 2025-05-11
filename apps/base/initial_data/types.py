from django.db import transaction
from django.db.models import Q
from apps.base.models.support import ARL, EPS, AccountType, AplicationStatus, BloodType, City, CivilStatus, ComercialCompanyType, ContractType, Country, DocType, FiscalResponsibility, Gender, HousingType, IndustryType, InvoiceStatus, JobType, NoveltyType, PaymentMethod, PensionFound, Periodicity, Priority, ProductType, RequestStatus, RetirementType, ServiceType, SeveranceWithdawalType, State, TaskType, TaxRegime, ThemeType, TransactionType
from apps.third_party.models.third_party import ThirdPartyType

print("Iniciando carga de datos de seleccion iniciales (TIPOS y ESTADOS)...")
def load_initial_types_and_statuses():
    """Carga los datos iniciales del sistema"""

    try:
        with transaction.atomic():
            # Tipos de Documento
            try:
                doc_types = [
                    ('CC', 'Cédula de Ciudadanía'),
                    ('CE', 'Cédula de Extranjería'),
                    ('PS', 'Pasaporte'),
                    ('TI', 'Tarjeta de Identidad'),
                    ('NIT', 'Número de Identificación Tributaria')
                ]
                for code, name in doc_types:
                    DocType.objects.get_or_create(
                        code=code,
                        defaults={'name': name}
                    )
                print("✅ Tipos de documento creados")
            except Exception as e:
                print('❌ Error al cargar los tipos de documento:', e)

            # Tipos de Preguntas para Encuestas
            try:
                from apps.surveys.models.surveymodel import QuestionType
                
                question_types = [
                    ('TEXT', 'Campo de texto simple'),
                    ('TEXT_AREA', 'Campo de texto multilínea'),
                    ('SINGLE_CHOICE', 'Selección única entre varias opciones'),
                    ('MULTIPLE_CHOICE', 'Selección múltiple entre varias opciones'),
                    ('RATING', 'Evaluación en escala'),
                    ('DATE', 'Selector de fecha'),
                    ('NUMBER', 'Campo numérico'),
                    ('YES_NO', 'Pregunta de Sí/No')
                ]
                
                for name, description in question_types:
                    QuestionType.objects.get_or_create(
                        name=name,
                        defaults={'description': description}
                    )
                print("✅ Tipos de preguntas creados")
            except Exception as e:
                print('❌ Error al cargar los tipos de preguntas:', e)

            # Tipos de Transacción
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
                print("✅ Tipos de transacción creados")
            except Exception as e:
                print('❌ Error al cargar los tipos de transacción:', e)

            # Tipos de Cuenta
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
                print("✅ Tipos de cuenta creados")
            except Exception as e:
                print('❌ Error al cargar los tipos de cuenta:', e)

            # Periodicidad
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
                print("✅ Periodicidades creadas")
            except Exception as e:
                print('❌ Error al cargar las periodicidades:', e)

            # Géneros
            try:
                genres = ['Masculino', 'Femenino', 'Otro']
                for name in genres:
                    Gender.objects.get_or_create(name=name)
                print("✅ Géneros creados")
            except Exception as e:
                print('❌ Error al cargar los géneros:', e)

            # Tipos de Sangre
            try:
                blood_types = [
                    ('+', 'O'), ('-', 'O'),
                    ('+', 'A'), ('-', 'A'),
                    ('+', 'B'), ('-', 'B'),
                    ('+', 'AB'), ('-', 'AB')
                ]
                for rh, abo in blood_types:
                    BloodType.objects.get_or_create(rh=rh, abo=abo)
                print("✅ Tipos de sangre creados")
            except Exception as e:
                print('❌ Error al cargar los tipos de sangre:', e)

            # Tipos de Contrato
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
                print("✅ Tipos de contrato creados")
            except Exception as e:
                print('❌ Error al cargar los tipos de contrato:', e)

            # Metodo de pago
            try:
                Payment_Method = [
                    ('E001','Efectivo'),
                    ('T002','Transferencia'),
                    ('TC03','Tarjeta de Crédito'),
                    ('TD04','Tarjeta de Débito')                    
                ]
                for code, name in Payment_Method:
                                
                    PaymentMethod.objects.get_or_create(name=name, code=code)
                print("✅ Metodos de pago creados")
            except Exception as e:
                print('❌ Error al cargar los metodos de pago:', e)

            #Estado Civil
            try:
                civil_status = [
                    ('S001','Soltero'),
                    ('C002','Casado'),
                    ('D003','Divorciado'),
                    ('V004','Viudo'),
                    ('U005','Unión Libre')
                ]
                for code, name in civil_status:
                    CivilStatus.objects.get_or_create(name=name, code=code)
                print("✅ Estados Civiles creados")
            except Exception as e:
                print('❌ Error al cargar los estados civiles:', e)

            # Tipos de Novedades
            try:
                novelty_types = [
                    ('Personal'),
                    ('Cita Medica'),
                    ('Dia Laboral'),
                    ('Vacaciones'),
                    ('Licencia por Calamidad'),
                    ('Licencia por Maternidad'),
                    ('Licencia por Paternidad'),
                    ('Licencia por Luto'),
                    ('Otros')
                ]
                for name in novelty_types:
                    NoveltyType.objects.get_or_create(name=name)
                print("✅ Tipos de novedad creados")
            except Exception as e:
                print('❌ Error al cargar los tipos de novedad:', e)
            

            # Tipos de Trabajo
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
                print("✅ Tipos de trabajo creados")                
            except Exception as e:
                print('❌ Error al cargar los tipos de trabajo:', e)

            # Tipos de Retiro de Cesantias
            try:
                severance_withdawal_types = [
                    ('Mejoramiento de Vivienda'),
                    ('Estudios'),
                    ('Compra de Vivienda'),
                    ('Finalizacion de Contrato'),
                ]            
                for name in severance_withdawal_types:
                    SeveranceWithdawalType.objects.get_or_create(
                        name=name
                    )
                print("✅ Tipos de Retiro de Cesantias creados")
            except Exception as e:
                print('❌ Error al cargar los tipos de Retiro de Cesantias:', e)

            #Tipo de Retiro laboral
            try:
                Retirement_Type = [
                    ('Retiro Voluntario'),
                    ('Termino de Contrato'),
                    ('Pension'),              
                ]
                for name in Retirement_Type:
                    RetirementType.objects.get_or_create(
                        name=name
                    )
                print("✅ Tipos de Retiro laboral creados")
            except Exception as e:
                print('❌ Error al cargar los tipos de Retiro laboral:', e)
            
            # Tipos de Vivienda
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
                print("✅ Tipos de vivienda creados")
            except Exception as e:
                print('❌ Error al cargar los tipos de vivienda:', e)
            #Tipos de Terceros
            try:
                third_party_types = [
                    ('CLI','Cliente'),
                    ('PRO','Proveedor'),
                    ('EMP','Empleado'),
                    ('ACC','Accionista'),
                    ('ASO','Contratista'),
                    ('OTR','Otro')
                ]
                for code,name in third_party_types:
                    ThirdPartyType.objects.get_or_create(
                        code=code,
                        defaults={'name': name}
                    )
                print("✅ Tipos de Terceros creados")
            except Exception as e:
                print('❌ Error al cargar los Tipos de Terceros:', e)
            # EPS
            try:
                ENTIDADES_EPS = [
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

                for code, name in ENTIDADES_EPS:
                    EPS.objects.create(code=code, name=name)
                print("✅ Datos de EPS cargados")

            except Exception as e:  
                print('❌ Error al cargar los datos iniciales:', e)

            # FONDO DE PENSIONES
            try:
                FONDO_PENSION   = [
                    (1, 'PROTECCION SA'),
                    (2, 'PORVENIR SA'),
                    (3, 'COLFONDOS'),
                    (4, 'COLPENSIONES'),
                    (5, 'OLD MUTUAL SA'),
                    (6, 'ASOCIACION COLOMBIANA DE AVIADORES CIVILES ACDAC'),
                    (7, 'ECOPETROL'),
                    (8, 'FONDO DE PRESTACIONES SOCIALES DEL MAGISTERIO'),
                ]

                for code, name in FONDO_PENSION:
                    PensionFound.objects.create(code=code, name=name)

                print("✅ Datos de Fondo de Pensiones cargados")

            except Exception as e:  
                print('❌ Error al cargar los datos iniciales:', e)

            # ARL
            try:
                ARL_OBJECT = [
                    (1,'ARL Sura'),
                    (2,'Seguros Positiva'),
                    (3,'Seguros Colpatria'),
                    (4,'ARL Colmena'),
                    (5,'Seguros Bolívar'),
                    (6,'ARL Alfa'),
                    (7,'ARL Aurora'),
                    (8,'ARL Liberty Seguros'),
                    (9,'ARL La Equidad'),
                    (10,'ARL Mapfre')
                ]

                for code, name in ARL_OBJECT:
                    ARL.objects.create(name=name)

                print("✅ Datos de ARL cargados")

            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)


            
            
            # Tipos eventos del sistema
            try:
                PRUDUCT_TYPE = [
                    ('ingreso'),
                    ('Salida'),
                    ('Cambio de Departamento'),
                    ('Cambio de Cargo'),
                    ('Cambio de Jefe'),
                    ('Cambio de Area'),
                    ('Cambio de Departamento'),
                    ('Cambio de Nivel'),
                ]
                for nombre in PRUDUCT_TYPE:
                    ProductType.objects.get_or_create(name=nombre)
                print('✅ Datos iniciales de Tipos de Eventos cargados.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)

            #Tipo de tareas
            try:
                TASK_TYPE = [
                    ('Llamada'),
                    ('Reunion'),
                    ('Correo Electronico')
                ]
                for nombre in TASK_TYPE:
                    TaskType.objects.get_or_create(name=nombre, )
                print('✅ Datos iniciales de Tipos de Tareas cargados.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)
            
            #Tipo de Producto
            try:
                PRODUCT_TYPE = [
                    ('Hardware'),
                    ('Software'),
                    ('Servicio'),
                    ('Software Libre'),
                    ('Componente'),
                    ('Licencia'),
                ]
                for nombre in PRODUCT_TYPE:
                    ServiceType.objects.get_or_create(name=nombre)
                print('✅ Datos iniciales de Tipos de Productos cargados.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)

            #Estado de Facturas
            try:
                INVOICE_STATUS =[
                    ('Pendiente'),
                    ('Pagada'),
                    ('Anulada'),
                    ('Enviada'),
                    ('Recibida'),
                    ('En Proceso'),
                    ('Rechazada'),
                    ('Revisada'),
                    ('En Revision'),
                    ('En Corte'),
                    ('Entregada'),
                    ('Aprobada'),
                    ('Revisada por Gerente'),
                    ('Rechazada por Gerente'),
                    ('Aprobada por Gerente'),
                    ('Enviada a Corte'),
                    ('Entregada a Corte'),
                    ('Aprobada a Corte'),
                    ('Revisada a Corte'),
                    ('Rechazada a Corte'),
                    ('Enviada a Aprobacion'),
                    ('Entregada a Aprobacion'),
                    ('Aprobada a Aprobacion'),
                    ('Revisada a Aprobacion'),
                ]
                for nombre in INVOICE_STATUS:
                    InvoiceStatus.objects.get_or_create(name=nombre)
                    print('✅ Datos iniciales de Estados de Facturas cargados.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)

            #Prioridades
            try:
                PRIORIDAD = [
                    ('Alta'),
                    ('Media'),
                    ('Baja'),
                ]
                for nombre in PRIORIDAD:
                    Priority.objects.get_or_create(name=nombre)
                    print('✅ Datos iniciales de Prioridades cargados.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)

            # Tipo de Industria
            try:
                INDUSTRIA = [
                    ('Agricultura'),
                    ('Alimentos'),
                    ('Construcción'),
                    ('Comercio'),
                    ('Servicios'),
                    ('Transporte'),
                    ('Informática'),
                    ('Educación'),
                    ('Salud'),
                    ('Finanzas'),
                    ('Manufactura'),
                    ('Otros'),
                ]
                for nombre in INDUSTRIA:
                    IndustryType.objects.get_or_create(name=nombre)
                    print('✅ Datos iniciales de Tipos de Industria cargados.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)


            # tema del template
            try:
                TEMAS = [
                    ('light', 'Claro'),
                    ('dark', 'Oscuro'),
                    ('system', 'Sistema'),
                ]
                for tema in TEMAS:
                    ThemeType.objects.get_or_create(name=tema[0], code=tema[1])
                print('✅ Datos iniciales de Temas cargados.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)

            # Estado de la solicutud
            try:
                STATUS_SOLICITUD = [
                    (1,'Abierta'),
                    (2,'En Proceso'),
                    (3,'Cerrada'),
                ]
                for status in STATUS_SOLICITUD:
                    RequestStatus.objects.get_or_create(name=status[0])
                print('✅ Datos iniciales de Estado de Solicitudes cargados.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)

            #Tipos de Graficos(ChartType)
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

            #Tipos de Regimen Fiscal
            try:
                REGIMEN_FISCAL = [
                    ('Régimen Comun', 'Régimen Ordinario'),
                    ('Régimen Simplificado', 'Régimen Simplificado'),
                    ('Régimen Especial', 'Régimen Especial'),
                ]
                for code, name in REGIMEN_FISCAL:
                    TaxRegime.objects.get_or_create(name=name, code=code)
                print('✅ Datos iniciales de Regímenes Fiscales cargados.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)

            #Tipos sociedad comercial
            try:
                SOCIEDADES = [
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
                for code, name in SOCIEDADES:
                    ComercialCompanyType.objects.get_or_create(name=name, code=code)
                print('✅ Datos iniciales de Sociedades cargados.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)
            
            #Responsabilidades fiscales
            try:
                RESPONSABILIDAD = [
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
                for code, name in RESPONSABILIDAD:
                    FiscalResponsibility.objects.get_or_create(name=name, code=code)
                print('✅ Datos iniciales de Responsabilidades fiscales cargados.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)

            # estado del tramite
            try:
                ESTADOS_SOLICITUD = [
                        (1, 'Pre Aprobado'),
                        (2, 'Aprobado'),
                        (3, 'Re agendado'),
                        (4, 'Cancelado'),
                        (5, 'En proceso'),
                        (6, 'Finalizado'),
                    ]
                for Estado in ESTADOS_SOLICITUD:
                    AplicationStatus.objects.get_or_create(name=Estado[1], code=Estado[0])
                print('✅ Datos iniciales de Estado de Tramites cargados.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)
            
            # Grupos de usuarios
            try:
                from django.contrib.auth.models import Group, Permission
                GRUPOS = [
                    ('Administrador', 'Administrador'),
                    ('Colaborador', 'Colaborador'),
                    ('Gerente', 'Gerente'),
                ]
                for grupo in GRUPOS:
                    Group.objects.get_or_create(name=grupo[0])
                print('✅ Datos iniciales de GRUPOS cargados.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)

            try:
                #agrega los permisos de usuario por defecto
                from django.contrib.auth.models import Permission
                from django.contrib.contenttypes.models import ContentType
        
                #agrega todos los permisos al usuario grupo Administrador
                grupo = Group.objects.get(name='Administrador')
                permisos = Permission.objects.all()
                grupo.permissions.add(*permisos)
                print('Permisos de Administrador cargados correctamente.')
                #agrega todos los permisos de listar y de crear al usuario grupo Colaborador
                grupo = Group.objects.get(name='Colaborador')
                colaborador_group = Group.objects.get(name='Colaborador')
                colaborador_permissions = Permission.objects.filter(
                    Q(codename__icontains='permiso') | Q(codename__icontains='vacaciones')
                )
                colaborador_group.permissions.add(*colaborador_permissions)
                print('✅ Permisos de Colaborador cargados correctamente.')
                from apps.base.models.users import User
                USUARIO = [
                    ('Administrador', '123456'),  # Include the username and password in the list
                    ]
                # Crear o obtener el grupo "Administrador"
                admin_group, created_group = Group.objects.get_or_create(name='Administrador')
                if created_group:
                    print(f"Grupo creado: {admin_group.name}")
                else:
                    print(f"Grupo existente: {admin_group.name}")
                for usuario in USUARIO:
                    user, created = User.objects.get_or_create(
                        username=usuario[0],
                        defaults={
                        'is_superuser': True,
                        'is_staff': True,  # Necesario para acceder al panel de administración
                        'email': 'correo@example.com'  # Si tienes un email asociado al usuario
                    }
                        )
                    if created:  # Only set the password if the user is newly created
                        user.set_password(usuario[1])  # Set the password using set_password method
                        user.save()
                        user.groups.add(admin_group)
                    print('✅ USUARIO INICIAL CREADO correctamente.')
            except Exception as e:
                print('❌ Error al cargar los datos iniciales:', e)
            
            print("✅ Datos iniciales cargados correctamente.")
    
    except Exception as e:
        print('❌ Error al ejecutar la carga de datos:', e)
load_initial_types_and_statuses()