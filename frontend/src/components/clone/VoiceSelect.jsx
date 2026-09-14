import SearchableSelect from '../SearchableSelect';

export default function VoiceSelect({
  id,
  label,
  value,
  onChange,
  options,
  groups = [],
  optionLabel = (option) => option.label ?? option,
  disabled = false,
  optionIcon,
}) {
  const normalizeOption = (option, group) => {
    const key = typeof option === 'string' ? option : option.value;
    return {
      value: key,
      label: optionLabel(option),
      ...(group ? { group: group.label, groupLabel: group.label } : {}),
    };
  };

  const searchableOptions = [
    ...options.map((option) => normalizeOption(option)),
    ...groups.flatMap((group) => group.options.map((option) => normalizeOption(option, group))),
  ];

  // Restored profiles can contain a valid value outside today's curated
  // choices. Keep it visible and selectable instead of showing a blank value.
  if (value && !searchableOptions.some((option) => option.value === value)) {
    searchableOptions.unshift({ value, label: value });
  }

  const renderOption = (option) => {
    const Icon = optionIcon?.(option.value);
    return (
      <span className="inline-flex items-center gap-2">
        {Icon && <Icon size={16} aria-hidden="true" className="shrink-0 opacity-75" />}
        <span>{option.label}</span>
      </span>
    );
  };

  return (
    <SearchableSelect
      id={id}
      value={value}
      onChange={onChange}
      options={searchableOptions}
      disabled={disabled}
      ariaLabel={label}
      renderLabel={(option) => option.label}
      renderOption={renderOption}
      renderGroupHeaders={groups.length > 0}
      menuPortal
      buttonClassName="min-h-12 border-transparent bg-[var(--chrome-hover-bg)] px-3 text-sm text-[var(--chrome-fg)] shadow-none hover:bg-[var(--chrome-accent-bg)]"
    />
  );
}
