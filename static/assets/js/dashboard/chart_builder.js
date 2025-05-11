// chart_builder.js
class ChartBuilder {
    constructor(config) {
      this.models = config.models;
      this.chartTypes = config.chartTypes;
      this.existingData = config.existingData || null;
      this.chartInstance = null;
    }
  
    init() {
      this.initSelectors();
      this.bindEvents();
      if (this.existingData) this.loadExistingData();
    }
  
    initSelectors() {
      this.select2Config = {
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: this.trans('select_field')
      };
      
      $('#modelSelect, #chartType').select2(this.select2Config);
    }
  
    bindEvents() {
      $('#modelSelect').on('change', () => this.handleModelChange());
      $('#saveChartBtn').click(() => this.saveChart());
    }
  
    async handleModelChange() {
      const model = this.getSelectedModel();
      if (!model) return;
      
      try {
        const fields = await this.fetchModelFields(model);
        this.renderFieldOptions(fields);
        this.toggleSections(true);
      } catch (error) {
        this.showError(this.trans('error_load_fields'));
      }
    }
  
    renderFieldOptions(fields) {
      this.renderOptions('#xAxisField', this.filterFields(fields, 'xAxis'));
      this.renderOptions('#yAxisField', [
        {value: 'count', text: this.trans('record_count')},
        ...this.filterFields(fields, 'yAxis')
      ]);
    }
  
    filterFields(fields, type) {
      const filters = {
        xAxis: ['CharField', 'DateField', 'ForeignKey'],
        yAxis: ['IntegerField', 'FloatField', 'DecimalField']
      };
      return fields.filter(f => filters[type].includes(f.type));
    }
  
    async saveChart() {
      const formData = this.getFormData();
      if (!this.validateForm(formData)) return;
  
      try {
        const response = await this.apiSaveChart(formData);
        window.location = response.detailUrl;
      } catch (error) {
        this.showError(error.message);
      }
    }
  
    getFormData() {
      return {
        title: $('#chartTitle').val(),
        description: $('#chartDescription').val(),
        chartType: $('#chartType').val(),
        model: $('#modelSelect').val(),
        xAxis: $('#xAxisField').val(),
        yAxis: $('#yAxisField').val(),
        filters: this.collectFilters(),
        config: this.collectAdvancedConfig()
      };
    }
  }
  
  function initChartBuilder(config) {
    const builder = new ChartBuilder(config);
    builder.init();
  }