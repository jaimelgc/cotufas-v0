export function toDateTime(date: string, time: string): Date {
  return new Date(`${date}T${time}`);
}

export function formatShowtime(date: string, time: string): string {
  return toDateTime(date, time).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatShowdate(date: string, time: string): string {
  return toDateTime(date, time).toLocaleDateString([], {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}