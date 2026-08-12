import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';
import { COUNTERPARTIES_CONFIG } from '../counterparties/counterparties.config';

/** doc §2.5 "item master" -- consumables and linen/amenity stock. `stock_tracked`
 * (Q267) decides whether an item goes through the full movement ledger below, or
 * is meant to be expensed directly at the point of purchase instead (that posting
 * is Bills' job -- not built here, Bills doesn't exist yet).
 *
 * `quantity_on_hand`, `weighted_average_cost` and `total_value` are backend-computed
 * from the movement ledger (receipts minus issues/wastage, plus/minus count
 * adjustments; valuation is the quantity-weighted mean of receipt unit costs,
 * doc §2.5 "weighted average" [CONFIRM]) -- not editable here, hence showInForm:false. */
export const INVENTORY_ITEMS_CONFIG: EntityPageConfig = {
  title: 'Inventory Items',
  subtitle: 'Item master (doc §2.5) -- consumables, linen and amenities. Stock-tracked items carry a running balance; others are expensed on purchase.',
  resourcePath: 'inventory-items',
  fields: [
    { key: 'code', label: 'Code', type: 'text', required: true, gridWidth: 110 },
    { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 220 },
    { key: 'category', label: 'Category', type: 'text', gridWidth: 140 },
    { key: 'unit_of_measure', label: 'Unit of measure', type: 'text', gridWidth: 130 },
    { key: 'reorder_level', label: 'Reorder level', type: 'number', gridWidth: 130 },
    { key: 'stock_tracked', label: 'Stock-tracked', type: 'boolean', gridWidth: 120 },
    {
      key: 'default_supplier_id',
      label: 'Default supplier',
      type: 'relation-select',
      relationResourcePath: 'counterparties',
      relationLabelKey: 'name',
      relationCreateFields: COUNTERPARTIES_CONFIG.fields,
      showInGrid: false,
    },
    { key: 'default_supplier_name', label: 'Default supplier', type: 'text', showInForm: false, gridWidth: 170 },
    { key: 'quantity_on_hand', label: 'Qty on hand', type: 'number', showInForm: false, gridWidth: 120, sortable: false },
    { key: 'weighted_average_cost', label: 'Weighted avg. cost (AED)', type: 'number', showInForm: false, gridWidth: 170, sortable: false },
    { key: 'total_value', label: 'Total value (AED)', type: 'number', showInForm: false, gridWidth: 150, sortable: false },
    { key: 'notes', label: 'Notes', type: 'textarea', showInGrid: false },
    { key: 'active', label: 'Active', type: 'boolean', gridWidth: 90 },
  ],
};

/** doc §2.5 stock ledger -- "Stock movements are mandatory, not optional." One row
 * per receipt/issue/transfer/wastage/count event; a stock count's variance is
 * itself a 'count_adjustment' movement (positive or negative quantity) rather than
 * a separate expected-vs-actual object.
 *
 * Location is `location_type` + a free-text `location_reference` (doc §2.5:
 * "central store, building, unit, or UnitSpace") rather than a polymorphic FK --
 * the shared form doesn't have a dynamic-relation-picker yet, and a typed
 * reference (e.g. a unit code) is enough to make "stock by location" real without
 * that machinery. `to_location_*` and `unit_cost`/supplier only apply to transfers
 * and receipts respectively -- shown conditionally via `visibleWhen`. */
export const INVENTORY_MOVEMENTS_CONFIG: EntityPageConfig = {
  title: 'Inventory Movements',
  subtitle: 'Receipts, issues, transfers, wastage and stock-count adjustments (doc §2.5) -- the ledger behind each item’s balance.',
  resourcePath: 'inventory-movements',
  fields: [
    {
      key: 'item_id',
      label: 'Item',
      type: 'relation-select',
      required: true,
      relationResourcePath: 'inventory-items',
      relationLabelKey: 'name',
      showInGrid: false,
    },
    { key: 'item_code', label: 'Item code', type: 'text', showInForm: false, gridWidth: 110 },
    { key: 'item_name', label: 'Item', type: 'text', showInForm: false, gridWidth: 180 },
    {
      key: 'movement_type',
      label: 'Type',
      type: 'select',
      required: true,
      options: [
        { label: 'Receipt', value: 'receipt' },
        { label: 'Issue', value: 'issue' },
        { label: 'Transfer', value: 'transfer' },
        { label: 'Wastage', value: 'wastage' },
        { label: 'Count adjustment', value: 'count_adjustment' },
      ],
      gridWidth: 150,
    },
    { key: 'date', label: 'Date', type: 'date', required: true, gridWidth: 120 },
    { key: 'quantity', label: 'Quantity', type: 'number', required: true, gridWidth: 110 },
    {
      key: 'location_type',
      label: 'Location type',
      type: 'select',
      required: true,
      options: [
        { label: 'Central store', value: 'central_store' },
        { label: 'Building', value: 'building' },
        { label: 'Unit', value: 'unit' },
        { label: 'Unit space', value: 'unit_space' },
      ],
      gridWidth: 140,
    },
    { key: 'location_reference', label: 'Location reference', type: 'text', gridWidth: 170 },
    {
      key: 'to_location_type',
      label: 'Transfer to: location type',
      type: 'select',
      options: [
        { label: 'Central store', value: 'central_store' },
        { label: 'Building', value: 'building' },
        { label: 'Unit', value: 'unit' },
        { label: 'Unit space', value: 'unit_space' },
      ],
      showInGrid: false,
      visibleWhen: { field: 'movement_type', equals: 'transfer' },
    },
    {
      key: 'to_location_reference',
      label: 'Transfer to: location reference',
      type: 'text',
      showInGrid: false,
      visibleWhen: { field: 'movement_type', equals: 'transfer' },
    },
    {
      key: 'unit_cost',
      label: 'Unit cost (AED)',
      type: 'number',
      showInGrid: false,
      visibleWhen: { field: 'movement_type', equals: 'receipt' },
    },
    {
      key: 'supplier_id',
      label: 'Supplier',
      type: 'relation-select',
      relationResourcePath: 'counterparties',
      relationLabelKey: 'name',
      relationCreateFields: COUNTERPARTIES_CONFIG.fields,
      showInGrid: false,
      visibleWhen: { field: 'movement_type', equals: 'receipt' },
    },
    { key: 'supplier_name', label: 'Supplier', type: 'text', showInForm: false, showInGrid: false },
    { key: 'reference', label: 'Reference', type: 'text', showInGrid: false },
    { key: 'notes', label: 'Notes', type: 'textarea', showInGrid: false },
  ],
};
