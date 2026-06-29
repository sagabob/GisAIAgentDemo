function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function buildLink(url: string, text: string): string {
  return `<a href="${url}" target="_blank" rel="noopener noreferrer">${text}</a>`;
}

export function formatChatMessageHtml(content: string): string {
  const links: string[] = [];
  let result = escapeHtml(content);

  const stashLink = (html: string): string => {
    const token = `@@LINK${links.length}@@`;
    links.push(html);
    return token;
  };

  result = result.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, (_, text, url) =>
    stashLink(buildLink(url, text)),
  );

  result = result.replace(/https?:\/\/maps\.google\.com\/[^\s<]+/g, (url) => {
    const cleanUrl = url.replace(/[),.;*]+$/g, '');
    return stashLink(buildLink(cleanUrl, 'View on Google Maps'));
  });

  result = result.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  result = result.replace(/\n/g, '<br>');

  links.forEach((link, index) => {
    result = result.replace(`@@LINK${index}@@`, link);
  });

  return result;
}
