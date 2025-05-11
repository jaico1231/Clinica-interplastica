document.addEventListener('DOMContentLoaded', () => {
  const dataTableBody = document.querySelector('#data-table tbody');
  const dataTable = document.getElementById('data-table');

  const puc_group = [
    { code: 1, name: 'ACTIVO' },
    { code: 2, name: 'PASIVO' },
    { code: 3, name: 'PATRIMONIO' },
    { code: 4, name: 'INGRESOS' },
    { code: 5, name: 'GASTOS' },
    { code: 6, name: 'COSTO DE VENTA' },
    { code: 7, name: 'COSTO DE PRODUCCION Y OPERACION' },
    { code: 8, name: 'CUENTAS DE ORDEN DEUDORAS' },
    { code: 9, name: 'CUENTAS DE ORDEN ACREEDORAS' },
  ];

  const puc_mayor = [
    { code: 11, name: 'DISPONIBLE' },
    { code: 12, name: 'INVERSIONES' },
    { code: 13, name: 'DEUDORES' },
    { code: 14, name: 'INVENTARIOS' },
    { code: 15, name: 'PROPIEDADES, PLANTA Y EQUIPO' },
    { code: 16, name: 'INTANGIBLES' },
    { code: 17, name: 'DIFERIDOS' },
    { code: 18, name: 'OTROS ACTIVOS' },
    { code: 19, name: 'VALORIZACIONES' },
    { code: 21, name: 'OBLIGACIONES FINANCIERAS' },
  ];

  const puc_subaccount = [
    { code: 1105, name: 'CAJA' },
    { code: 1110, name: 'BANCOS' },
    { code: 1115, name: 'REMESAS EN TRÁNSITO' },
    { code: 1120, name: 'CUENTAS DE AHORRO' },
    { code: 1125, name: 'FONDOS' },
    { code: 1205, name: 'ACCIONES' },
    { code: 1210, name: 'CUOTAS O PARTES DE INTERÉS SOCIAL' },
    { code: 1215, name: 'BONOS' },
  ];

  const puc_detailaccount = [
    { code: 110505, name: 'Caja general' },
    { code: 110510, name: 'Cajas menores' },
    { code: 110515, name: 'Moneda extranjera' },
    { code: 111005, name: 'Moneda nacional' },
    { code: 111010, name: 'Moneda extranjera' },
    { code: 111505, name: 'Moneda nacional' },
    { code: 111510, name: 'Moneda extranjera' },
    { code: 112005, name: 'Bancos' },
  ];


  function renderTable() {
    dataTableBody.innerHTML = ''; // Clear existing table rows

    // Combine all data arrays
    const allData = [
      ...puc_group,
      ...puc_mayor,
      ...puc_subaccount,
      ...puc_detailaccount
    ];

    allData.forEach(item => {
      const row = document.createElement('tr');
      row.innerHTML = `<td>${item.code}</td><td>${item.name}</td>`;
      dataTableBody.appendChild(row);
    });
  }

  renderTable(); // Initial render

  // Hide form and model selection
  document.getElementById('model-selector').style.display = 'none';
  document.getElementById('form-container').style.display = 'none';
});