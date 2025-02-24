let globalPopup = null;
let globalPopupInner = null;
let previousCard = null;
const activePromptTextarea = {};
const re_extranet = /<([^:]+:[^:]+):[\d\.]+>/;
const re_extranet_g = /\s+<([^:]+:[^:]+):[\d\.]+>/g;

const getENActiveTab = () => gradioApp().getElementById('tab_txt2img').style.display === 'block' ? 'txt2img' : 'img2img';

function requestGet(url, data, handler, errorHandler) {
  const xhr = new XMLHttpRequest();
  const args = Object.keys(data).map((k) => `${encodeURIComponent(k)}=${encodeURIComponent(data[k])}`).join('&');
  xhr.open('GET', `${url}?${args}`, true);
  xhr.onreadystatechange = () => {
    if (xhr.readyState === 4) {
      if (xhr.status === 200) {
        try {
          const js = JSON.parse(xhr.responseText);
          handler(js);
        } catch (error) {
          console.error(error);
          errorHandler();
        }
      } else {
        errorHandler();
      }
    }
  };
  const js = JSON.stringify(data);
  xhr.send(js);
}

function popup(contents) {
  if (!globalPopup) {
    globalPopup = document.createElement('div');
    globalPopup.onclick = () => { globalPopup.style.display = 'none'; };
    globalPopup.classList.add('global-popup');
    const close = document.createElement('div');
    close.classList.add('global-popup-close');
    close.onclick = () => { globalPopup.style.display = 'none'; };
    close.title = 'Close';
    globalPopup.appendChild(close);
    globalPopupInner = document.createElement('div');
    globalPopupInner.onclick = (event) => { event.stopPropagation(); return false; };
    globalPopupInner.classList.add('global-popup-inner');
    globalPopup.appendChild(globalPopupInner);
    gradioApp().appendChild(globalPopup);
  }
  globalPopupInner.innerHTML = '';
  globalPopupInner.appendChild(contents);
  globalPopup.style.display = 'flex';
}

function readCardMetadata(event, extraPage, cardName) {
  requestGet('./sd_extra_networks/metadata', { page: extraPage, item: cardName }, (data) => {
    if (data?.metadata) {
      if (typeof (data?.metadata) !== 'string') data.metadata = JSON.stringify(data.metadata, null, 2);
      const elem = document.createElement('pre');
      elem.classList.add('popup-metadata');
      elem.textContent = data.metadata;
      popup(elem);
    }
  }, () => { });
  event.stopPropagation();
  event.preventDefault();
}

function readCardTags(el, tags) {
  const clickTag = (e, tag) => {
    e.preventDefault();
    e.stopPropagation();
    const textarea = activePromptTextarea[getENActiveTab()];
    if (textarea.value.indexOf(tag) !== -1) textarea.value = textarea.value.replace(tag, '');
    else textarea.value += ` ${tag}`;
    updateInput(textarea);
  };
  if (tags.length === 0) return;
  const cardTags = tags.split('|');
  if (cardTags.length === 0) return;
  const tagsEl = el.getElementsByClassName('tags')[0];
  if (tagsEl.children.length > 0) return;
  for (const tag of cardTags) {
    const span = document.createElement('span');
    span.classList.add('tag');
    span.textContent = tag;
    span.onclick = (e) => clickTag(e, tag);
    tagsEl.appendChild(span);
  }
}

function readCardInformation(event, extraPage, cardName) {
  requestGet('./sd_extra_networks/info', { page: extraPage, item: cardName }, (data) => {
    if (data?.info && (typeof (data?.info) === 'string')) {
      const elem = document.createElement('pre');
      elem.classList.add('popup-metadata');
      elem.textContent = data.info;
      popup(elem);
    }
  }, () => { });
  event.stopPropagation();
  event.preventDefault();
}

function readCardDescription(filename, descript) {
  const tabname = getENActiveTab();
  const fn = gradioApp().querySelector(`#${tabname}_description_filename  > label > textarea`);
  const description = gradioApp().querySelector(`#${tabname}_description > label > textarea`);
  fn.value = filename;
  description.value = descript?.trim() || '';
  description.focus();
  updateInput(fn);
  updateInput(description);
}

function saveCardPreview(event) {
  const tabname = getENActiveTab();
  const textarea = gradioApp().querySelector(`#${tabname}_preview_filename  > label > textarea`);
  const button = gradioApp().getElementById(`${tabname}_save_preview`);
  const el = event?.target?.parentElement?.parentElement?.parentElement;
  if (el?.classList?.contains('card')) {
    textarea.value = el.dataset.filename;
    updateInput(textarea);
    button.click();
  }
  event.stopPropagation();
  event.preventDefault();
}

function saveCardDescription(event) {
  const tabname = getENActiveTab();
  const el = event?.target?.parentElement?.parentElement?.parentElement;
  if (el?.classList?.contains('card')) el.dataset.description = gradioApp().getElementById(`${tabname}_description`)?.children[0].children[1].value;
  const button = gradioApp().getElementById(`${tabname}_save_description`);
  button.click();
  event.stopPropagation();
  event.preventDefault();
}

async function filterExtraNetworksForTab(tabname, searchTerm) {
  let found = 0;
  let items = 0;
  const t0 = performance.now();
  const cards = Array.from(gradioApp().querySelectorAll(`#${tabname}_extra_tabs div.card`));
  cards.forEach((elem) => {
    items += 1;
    if (searchTerm === '') {
      elem.style.display = '';
    } else {
      let text = `${elem.querySelector('.name').textContent.toLowerCase()} ${elem.querySelector('.search_term').textContent}`;
      text = text.toLowerCase().replace('models--', 'Diffusers').replace('\\', '/');
      if (text.indexOf(searchTerm) === -1) {
        elem.style.display = 'none';
      } else {
        elem.style.display = '';
        found += 1;
      }
    }
  });
  const t1 = performance.now();
  if (found > 0) log(`filterExtraNetworks: text=${searchTerm} items=${items} match=${found} time=${Math.round(1000 * (t1 - t0)) / 1000000}`);
  else log(`filterExtraNetworks: text=all items=${items} time=${Math.round(1000 * (t1 - t0)) / 1000000}`);
}

function setupExtraNetworksForTab(tabname) {
  gradioApp().querySelector(`#${tabname}_extra_tabs`).classList.add('extra-networks');
  const tabs = gradioApp().querySelector(`#${tabname}_extra_tabs > div`);
  const search = gradioApp().querySelector(`#${tabname}_extra_search textarea`);
  const refresh = gradioApp().getElementById(`${tabname}_extra_refresh`);
  const description = gradioApp().getElementById(`${tabname}_description`);
  const close = gradioApp().getElementById(`${tabname}_extra_close`);
  const en = gradioApp().getElementById(`${tabname}_extra_networks`);
  search.classList.add('search');
  description.classList.add('description');
  tabs.appendChild(refresh);
  tabs.appendChild(close);
  const div = document.createElement('div');
  div.classList.add('second-line');
  tabs.appendChild(div);
  div.appendChild(search);
  div.appendChild(description);
  let searchTimer = null;
  search.addEventListener('input', (evt) => {
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      filterExtraNetworksForTab(tabname, search.value.toLowerCase());
      searchTimer = null;
    }, 150);
  });

  let hoverTimer = null;
  gradioApp().getElementById(`${tabname}_extra_tabs`).onmouseover = (e) => {
    const el = e.target.closest('.card'); // bubble-up to card
    if (!el || (el.title === previousCard)) return;
    if (!hoverTimer) {
      hoverTimer = setTimeout(() => {
        readCardDescription(el.dataset.filename, el.dataset.description);
        readCardTags(el, el.dataset.tags);
        previousCard = el.title;
      }, 300);
    }
    el.onmouseout = () => {
      clearTimeout(hoverTimer);
      hoverTimer = null;
    };
  };

  const intersectionObserver = new IntersectionObserver((entries) => {
    if (!en) return;
    for (const el of Array.from(gradioApp().querySelectorAll('.extra-networks-page'))) {
      el.style.height = `${window.opts.extra_networks_height}vh`;
      el.parentElement.style.width = '-webkit-fill-available';
    }
    if (entries[0].intersectionRatio > 0) {
      if (window.opts.extra_networks_card_cover === 'cover') {
        en.style.transition = '';
        en.style.zIndex = 100;
        en.style.position = 'absolute';
        en.style.right = 'unset';
        en.style.width = 'unset';
        en.style.height = 'unset';
        gradioApp().getElementById(`${tabname}_settings`).parentNode.style.width = 'unset';
      } else if (window.opts.extra_networks_card_cover === 'sidebar') {
        en.style.transition = 'width 0.2s ease';
        en.style.zIndex = 100;
        en.style.position = 'absolute';
        en.style.right = '0';
        en.style.width = `${window.opts.extra_networks_sidebar_width}vw`;
        en.style.height = '-webkit-fill-available';
        gradioApp().getElementById(`${tabname}_settings`).parentNode.style.width = `${100 - 2 - window.opts.extra_networks_sidebar_width}vw`;
      } else {
        en.style.transition = '';
        en.style.zIndex = 0;
        en.style.position = 'relative';
        en.style.right = 'unset';
        en.style.width = 'unset';
        en.style.height = 'unset';
        gradioApp().getElementById(`${tabname}_settings`).parentNode.style.width = 'unset';
      }
    } else {
      en.style.width = 0;
      gradioApp().getElementById(`${tabname}_settings`).parentNode.style.width = 'unset';
    }
  });
  intersectionObserver.observe(en); // monitor visibility of
}

function setupExtraNetworks() {
  setupExtraNetworksForTab('txt2img');
  setupExtraNetworksForTab('img2img');

  function registerPrompt(tabname, id) {
    const textarea = gradioApp().querySelector(`#${id} > label > textarea`);
    if (!activePromptTextarea[tabname]) activePromptTextarea[tabname] = textarea;
    textarea.addEventListener('focus', () => { activePromptTextarea[tabname] = textarea; });
  }

  registerPrompt('txt2img', 'txt2img_prompt');
  registerPrompt('txt2img', 'txt2img_neg_prompt');
  registerPrompt('img2img', 'img2img_prompt');
  registerPrompt('img2img', 'img2img_neg_prompt');
  log('initExtraNetworks');
}

function tryToRemoveExtraNetworkFromPrompt(textarea, text) {
  let m = text.match(re_extranet);
  let replaced = false;
  let newTextareaText;
  if (m) {
    const partToSearch = m[1];
    newTextareaText = textarea.value.replaceAll(re_extranet_g, (found) => {
      m = found.match(re_extranet);
      if (m[1] === partToSearch) {
        replaced = true;
        return '';
      }
      return found;
    });
  } else {
    newTextareaText = textarea.value.replaceAll(new RegExp(text, 'g'), (found) => {
      if (found === text) {
        replaced = true;
        return '';
      }
      return found;
    });
  }
  if (replaced) {
    textarea.value = newTextareaText;
    return true;
  }
  return false;
}

function refreshExtraNetworks(tabname) {
  console.log('refreshExtraNetworks', tabname, gradioApp().querySelector(`#${tabname}_extra_networks textarea`)?.value);
  gradioApp().querySelector(`#${tabname}_extra_networks textarea`)?.dispatchEvent(new Event('input'));
}

function cardClicked(textToAdd, allowNegativePrompt) {
  const tabname = getENActiveTab();
  const textarea = allowNegativePrompt ? activePromptTextarea[tabname] : gradioApp().querySelector(`#${tabname}_prompt > label > textarea`);
  if (textarea.value.indexOf(textToAdd) !== -1) textarea.value = textarea.value.replace(textToAdd, '');
  else textarea.value += textToAdd;
  updateInput(textarea);
}

function extraNetworksSearchButton(event) {
  const tabname = getENActiveTab();
  const searchTextarea = gradioApp().querySelector(`#${tabname}_extra_tabs > div > div > textarea`);
  const button = event.target;
  const text = button.classList.contains('search-all') ? '' : `/${button.textContent.trim()}/`;
  searchTextarea.value = text;
  updateInput(searchTextarea);
}

function getENActivePage() {
  const tabname = getENActiveTab();
  const page = gradioApp().querySelector(`#${tabname}_extra_networks > .tabs > .tab-nav > .selected`);
  return page ? page.innerText : '';
}

let desiredStyle = '';
function selectStyle(name) {
  desiredStyle = name;
  const tabname = getENActiveTab();
  const button = gradioApp().querySelector(`#${tabname}_styles_select`);
  button.click();
}

function applyStyles(styles) {
  let newStyles = [];
  if (styles) newStyles = Array.isArray(styles) ? styles : [styles];
  const index = newStyles.indexOf(desiredStyle);
  if (index > -1) newStyles.splice(index, 1);
  else newStyles.push(desiredStyle);
  return newStyles.join('|');
}

onUiLoaded(setupExtraNetworks);
