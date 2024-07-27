import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { $el } from "../../scripts/ui.js";
import * as util from "./libs/util.min.js";

let isInitialized = false;
let CLASS_NAME = "Model DB";
let DEFAULT_VALUES = {};
let DEFAULT_KEYS = [
  "positive",
  "negative",
  "seed",
  "control_after_generate",
  "steps",
  "cfg",
  "sampler_name",
  "scheduler",
  "denoise",
  "width",
  "height"
];
let db = {}; // { MODEL_NAME: { KEY: { ...OPEIONS }} }

async function getDefaultValues() {
  let response = await api.fetchApi("/shinich39/model-db/get-default-values", { cache: "no-store" });
  let data = await response.json();
  return data;
}

async function getData() {
  let response = await api.fetchApi("/shinich39/model-db/get-data", { cache: "no-store" });
  return await response.json();
}

async function setData(ckpt, key, values) {
  let response = await api.fetchApi("/shinich39/model-db/set-data", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ckpt, key, values }),
  });

  if (response.status !== 200) {
    throw new Error(response.statusText);
  }

  return await response.json();
}

async function removeData(ckpt, key) {
  let response = await api.fetchApi("/shinich39/model-db/remove-data", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ckpt, key }),
  });

  if (response.status !== 200) {
    throw new Error(response.statusText);
  }

  return await response.json();
}

function getCurrentKey() {
  let date = new Date();
  let month = date.getMonth() + 1;
  let day = date.getDate();
  let hour = date.getHours();
  let minute = date.getMinutes();
  let second = date.getSeconds();

  month = month >= 10 ? month : '0' + month;
  day = day >= 10 ? day : '0' + day;
  hour = hour >= 10 ? hour : '0' + hour;
  minute = minute >= 10 ? minute : '0' + minute;
  second = second >= 10 ? second : '0' + second;

  return date.getFullYear() + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':' + second;
}

function getKeys(ckpt) {
  return db[ckpt] ? Object.keys(db[ckpt]) : [];
}

function getValues(ckpt, key) {
  return db[ckpt]?.[key] || util.copy(DEFAULT_VALUES);
}

function getNodeValues(node) {
  let values = {};
  for (const k of DEFAULT_KEYS) {
    const w = node.widgets.find(e => e.name === k);
    values[k] = w ? w.value : DEFAULT_VALUES[k];
  }
  return values;
}

function updateKeys(node) {
  const ckptWidget = node.widgets.find(function(item) {
    return item.name === "ckpt_name";
  });

  const keyWidget = node.widgets.find(function(item) {
    return item.name === "key";
  });

  let ckpt = ckptWidget.value;
  let key = keyWidget.value;
  keyWidget.options.values = getKeys(ckpt);
  if (!key || keyWidget.options.values.indexOf(key) === -1) {
    keyWidget.value = keyWidget.options.values?.[keyWidget.options.values.length - 1] || `NO_KEY`;
    return true;
  } else {
    return false;
  }
}

function updateValues(node) {
  const ckptWidget = node.widgets.find(function(item) {
    return item.name === "ckpt_name";
  });

  const keyWidget = node.widgets.find(function(item) {
    return item.name === "key";
  });

  let ckpt = ckptWidget.value;
  let key = keyWidget.value;
  let values = getValues(ckpt, key);
  for (const [k, v] of Object.entries(values)) {
    const w = node.widgets.find(e => e.name === k);
    if (w) {
      w.value = v;
    }
  }
}

function updateNode(node) {
  const isKeyUpdated = updateKeys(node);
  if (isKeyUpdated) {
    updateValues(node);
  }
}

function updateNodes() {
  for (const node of app.graph._nodes) {
    try {
      if (node.comfyClass !== CLASS_NAME) {
        continue;
      }
      updateNode(node);
    } catch(err) {
      console.error(err);
    }
  }
}

app.registerExtension({
	name: "shinich39.ModelDB",
  setup() {
    // init, update old nodes
    getDefaultValues()
      .then((e) => { DEFAULT_VALUES = e; })
      .then(getData)
      .then((e) => { db = e; })
      .then(() => { isInitialized = true; })
      .then(updateNodes);
  },
  nodeCreated(node) {
    try {
      if (node.comfyClass !== CLASS_NAME) {
        return;
      }

      const ckptWidget = node.widgets.find(function(item) {
        return item.name === "ckpt_name";
      });

      const keyWidget = node.widgets.find(function(item) {
        return item.name === "key";
      });

      const posWidget = node.widgets.find(function(item) {
        return item.name === "positive";
      });
      posWidget.options.getMinHeight = () => 128;
      // posWidget.options.getMaxHeight = () => 256;

      const negWidget = node.widgets.find(function(item) {
        return item.name === "negative";
      });
      negWidget.options.getMinHeight = () => 128;
      // negWidget.options.getMaxHeight = () => 256;

      const addWidget = node.addWidget("button", "Add", null, addWidgetClickHandler, {
        serialize: false
      });
      addWidget.serializeValue = () => undefined;

      const removeWidget = node.addWidget("button", "Remove", null, removeWidgetClickHandler, {
        serialize: false
      });
      removeWidget.serializeValue = () => undefined;

      ckptWidget.callback = ckptWidgetChangeHandler;
      keyWidget.callback = keyWidgetChangeHandler;

      // change add widget position
      ;(function() {
        const prev = node.widgets.findIndex(e => e.name === "Add");
        const next = node.widgets.findIndex(e => e.name === "key") + 1;
        node.widgets.splice(next, 0, node.widgets.splice(prev, 1)[0]);
      })();

      // change remove widget position
      ;(function() {
        const prev = node.widgets.findIndex(e => e.name === "Remove");
        const next = node.widgets.findIndex(e => e.name === "key") + 2;
        node.widgets.splice(next, 0, node.widgets.splice(prev, 1)[0]);
      })();

      // the node created after initialize
      if (isInitialized) {
        updateNode(node);
      }

      function ckptWidgetChangeHandler(value) {
        updateKeys(node);
        updateValues(node);
      }
  
      function keyWidgetChangeHandler(value) {
        if (!value) {
          keyWidget.value = "NO_KEY";
        }
        // updateKeys(node);
        updateValues(node);
      }

      function addWidgetClickHandler() {
        let ckpt = ckptWidget.value;
        let key = getCurrentKey();
        let values = getNodeValues(node);

        setData(ckpt, key, values)
          .then(function(data) {
            db = data;
            keyWidget.options.values = getKeys(ckpt);
            keyWidget.value = key;
            updateValues(node);
          });
      }

      function removeWidgetClickHandler() {
        let ckpt = ckptWidget.value;
        let key = keyWidget.value;
        let idx = keyWidget.options.values.indexOf(key);

        if (keyWidget.options.values.length > 0 && idx > -1) {
          removeData(ckpt, key)
            .then(function(data) {
              db = data;
              keyWidget.options.values = getKeys(ckpt);
              idx = Math.min(idx, keyWidget.options.values.length - 1);
              keyWidget.value = idx > -1 ? keyWidget.options.values[idx] : "NO_KEY";
              updateValues(node);
            });
        }
      }
    } catch(err) {
      console.error(err);
    }
  }
});