-- indexes for common lookups and filters

create index idx_items_department_id on items (department_id);
create index idx_items_price on items (price);
create index idx_items_title on items (title);

create index idx_department_attributes_department_id on department_attributes (department_id);

create index idx_attribute_options_attribute_id on attribute_options (attribute_id);

create index idx_item_attributes_item_id on item_attributes (item_id);
create index idx_item_attributes_attribute_id on item_attributes (attribute_id);
create index idx_item_attributes_option_id on item_attributes (option_id);
