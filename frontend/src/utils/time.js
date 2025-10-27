const ISO_SECONDS_ONLY = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/;

const pad = (value) => String(value).padStart(2, '0');

export const toIsoLocalString = (input) => {
  if (!input && input !== 0) return '';
  if (typeof input === 'string' && ISO_SECONDS_ONLY.test(input)) {
    return input;
  }

  const date = input instanceof Date ? input : new Date(input);
  if (Number.isNaN(date.getTime())) {
    return typeof input === 'string' ? input : '';
  }

  return [
    date.getFullYear(),
    '-',
    pad(date.getMonth() + 1),
    '-',
    pad(date.getDate()),
    'T',
    pad(date.getHours()),
    ':',
    pad(date.getMinutes()),
    ':',
    pad(date.getSeconds()),
  ].join('');
};

export const normalizeTimestamp = (input) => {
  const iso = toIsoLocalString(input);
  return iso || undefined;
};
