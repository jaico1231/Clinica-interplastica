document.addEventListener('DOMContentLoaded', () => {
  const modelDropdown = document.getElementById('model-dropdown');
  const formContainer = document.getElementById('form-container');
  const dataForm = document.getElementById('data-form');
  const dataTableBody = document.querySelector('#data-table tbody');
  const dataTable = document.getElementById('data-table');

  let currentModel = null;
  let data = []; // Store data for each model

  modelDropdown.addEventListener('change', (event) => {
    const selectedModelName = event.target.value;
    currentModel = window.models.find(model => model.name === selectedModelName);

    if (currentModel) {
      generateForm(currentModel);
      loadData(currentModel.name);
    } else {
      dataForm.innerHTML = '';
      dataTableBody.innerHTML = '';
    }
  });

  function generateForm(model) {
    dataForm.innerHTML = ''; // Clear previous form

    model.fields.forEach(field => {
      const label = document.createElement('label');
      label.textContent = field.label;
      label.setAttribute('for', field.name);

      let input;
      if (field.type === 'textarea') {
        input = document.createElement('textarea');
      } else {
        input = document.createElement('input');
        input.type = field.type || 'text';
      }
      input.id = field.name;
      input.name = field.name;

      dataForm.appendChild(label);
      dataForm.appendChild(input);
    });

    const submitButton = document.createElement('button');
    submitButton.textContent = 'Guardar';
    submitButton.type = 'button';
    submitButton.addEventListener('click', saveData);
    dataForm.appendChild(submitButton);
  }

  function saveData() {
    if (!currentModel) return;

    const newDataItem = {};
    currentModel.fields.forEach(field => {
      const inputElement = document.getElementById(field.name);
      newDataItem[field.name] = inputElement.value;
    });

    data.push(newDataItem);
    saveDataToLocalStorage(currentModel.name);
    renderTable(currentModel);
    dataForm.reset();
  }

  function saveDataToLocalStorage(modelName) {
    localStorage.setItem(modelName, JSON.stringify(data));
  }

  function loadData(modelName) {
    const storedData = localStorage.getItem(modelName);
    data = storedData ? JSON.parse(storedData) : [];
    if (currentModel) {
      renderTable(currentModel);
    }
  }

  function renderTable(model) {
    dataTableBody.innerHTML = ''; // Clear existing table rows
    const thead = document.querySelector('#data-table thead tr');
    thead.innerHTML = '<th>Código</th><th>Nombre</th><th>Acciones</th>';

    model.fields.forEach(field => {
      const th = document.createElement('th');
      th.textContent = field.label;
      thead.appendChild(th);
    });

    data.forEach((item, index) => {
      const row = document.createElement('tr');

      let code = item[model.fields[0].name]
      let name = item[model.fields[1].name]

      row.innerHTML += `<td>${code}</td><td>${name}</td>`;

      // Add action buttons
      const actionsCell = document.createElement('td');
      actionsCell.classList.add('actions');

      const editButton = document.createElement('button');
      editButton.innerHTML = '<i class="fas fa-edit"></i> Editar';
      editButton.addEventListener('click', () => editItem(index));
      actionsCell.appendChild(editButton);

      const deleteButton = document.createElement('button');
      deleteButton.innerHTML = '<i class="fas fa-trash-alt"></i> Eliminar';
      deleteButton.addEventListener('click', () => deleteItem(index));
      actionsCell.appendChild(deleteButton);

      row.appendChild(actionsCell);

      model.fields.forEach(field => {
        const td = document.createElement('td');
        td.textContent = item[field.name] || '';
        row.appendChild(td);
      });

      dataTableBody.appendChild(row);
    });
  }

  function editItem(index) {
    // Implement edit functionality here
    alert(`Edit item at index ${index}`);
  }

  function deleteItem(index) {
    data.splice(index, 1);
    saveDataToLocalStorage(currentModel.name);
    renderTable(currentModel);
  }
});

