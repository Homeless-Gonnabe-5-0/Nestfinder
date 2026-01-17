// Simple parser to extract search parameters from user messages

export interface ParsedSearch {
  budget_min: number;
  budget_max: number;
  work_address: string;
  bedrooms: number;
  priorities: string[];
  max_commute_minutes: number;
  transport_mode: string;
}

export function parseUserMessage(message: string): ParsedSearch | null {
  const lower = message.toLowerCase();
  
  // Extract budget
  let budget_min = 0;
  let budget_max = 3000;
  
  const budgetMatch = lower.match(/\$?(\d+)\s*-?\s*\$?(\d+)?/);
  if (budgetMatch) {
    budget_min = parseInt(budgetMatch[1]);
    budget_max = budgetMatch[2] ? parseInt(budgetMatch[2]) : budget_min + 500;
  } else {
    const underMatch = lower.match(/under\s+\$?(\d+)/);
    if (underMatch) {
      budget_max = parseInt(underMatch[1]);
    }
  }
  
  // Extract bedrooms
  let bedrooms = 1;
  const bedroomMatch = lower.match(/(\d+)\s*[-\s]?bed/);
  if (bedroomMatch) {
    bedrooms = parseInt(bedroomMatch[1]);
  }
  
  // Extract work address
  let work_address = '';
  const addressMatch = message.match(/(?:work at|near|commute to)\s+([^,.\n]+)/i);
  if (addressMatch) {
    work_address = addressMatch[1].trim();
  }
  
  // If no address found, check for street numbers
  const streetMatch = message.match(/\d+\s+[A-Z][a-z]+\s+(?:St|Street|Ave|Avenue|Rd|Road)/i);
  if (streetMatch && !work_address) {
    work_address = streetMatch[0];
  }
  
  // Extract priorities
  const priorities: string[] = [];
  if (lower.includes('short commute') || lower.includes('close to work')) {
    priorities.push('short_commute');
  }
  if (lower.includes('safe') || lower.includes('safety')) {
    priorities.push('safe_area');
  }
  if (lower.includes('walkab') || lower.includes('walk')) {
    priorities.push('walkable');
  }
  if (lower.includes('quiet')) {
    priorities.push('quiet');
  }
  if (lower.includes('nightlife') || lower.includes('entertainment')) {
    priorities.push('nightlife');
  }
  if (lower.includes('cheap') || lower.includes('budget') || lower.includes('affordable')) {
    priorities.push('low_price');
  }
  
  // Default priorities if none found
  if (priorities.length === 0) {
    priorities.push('short_commute', 'low_price');
  }
  
  // Extract transport mode
  let transport_mode = 'transit';
  if (lower.includes('driv') || lower.includes('car')) {
    transport_mode = 'driving';
  } else if (lower.includes('bike') || lower.includes('cycling')) {
    transport_mode = 'biking';
  } else if (lower.includes('walk')) {
    transport_mode = 'walking';
  }
  
  // Extract max commute
  let max_commute_minutes = 45;
  const commuteMatch = lower.match(/(\d+)\s*(?:min|minute)/);
  if (commuteMatch) {
    max_commute_minutes = parseInt(commuteMatch[1]);
  }
  
  // Validate we have minimum required info
  if (!work_address) {
    return null;
  }
  
  return {
    budget_min,
    budget_max,
    work_address,
    bedrooms,
    priorities,
    max_commute_minutes,
    transport_mode,
  };
}
