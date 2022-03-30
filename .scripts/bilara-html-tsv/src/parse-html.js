(function(exports) {
  const fs = require('fs');
  const path = require('path');
  
  class ParseHtml {
    constructor(opts={}) {
      this.lang = opts.lang || 'root';
      this.verbose = opts.verbose;
    }

    parseIds(line) {
      let pparts = line.split(/id=['"]/);
      return pparts.length === 1
        ? []
        : pparts.slice(1).map(id=>id.replace(/['"].*/,''));
    }

    * htmlSegments(html, opts={}) {
      let { verbose=this.verbose } = opts;
      html = html.filter(line=>(
        !/DOCTYPE/.test(line) &&
        !/<\/?html>/.test(line) &&
        !/<\/?head>/.test(line) &&
        !/<\/?title>/.test(line) &&
        !/<\/?body>/.test(line) 
      ));

      let reSegment = /<segment/u;
      let reLine = /<p|<segment/u;
      let segmentLine = '';
      let i = 0;
      for (let line of html) {
        if (reSegment.test(segmentLine) && reLine.test(line)) {
          verbose && console.log(`htmlSegments${++i}:`, segmentLine);
          yield segmentLine;
          segmentLine = line;
        } else {
          segmentLine += line;
        }
      }
      if (segmentLine) {
        verbose && console.log(`htmlSegments${++i}:`, segmentLine, '[END]');
        yield segmentLine;
      }
    }

    * segmentsAsColumns(segHtml, opts={}) {
      let { verbose=this.verbose } = opts;
      let that = this;
      let segBase = '';
      let segNum = 0;
      let idMap = {};
      let hNum = [0,1,1,1,1,1,1];
      let hLevel = 0;
      let html = '';
      let h = '';
      let articleId = '';
      let para = 0;

      for (let line of segHtml) {
        if (!/<segment/.test(line)) {
          throw new Error(`unexpected raw HTML input:${line}`);
        } 
        
        line = line.trim();
        let segmentParts = line.split('<segment').map(part=>{
          let tail = part.replace(/.*<.segment>/u, '');
          return tail;
        });
        html += segmentParts.join('{}');

        let ids = that.parseIds(line);

        let segment_id = ids.filter(id=>/:/.test(id)).slice(-1)[0];
        if (/<article/.test(line)) { // initialize numbering
          articleId = ids[0] || "ARTICLE_ID_REQUIRED";
          segNum = 1;
          segBase = `${articleId}:${para}`;
          verbose && console.log(`segmentToColumns() article:`,
            JSON.stringify({articleId, segBase, segNum}));
        } 
        if (segment_id) { // segment override
          let idParts = segment_id.split('.');
          segNum = Number(idParts.pop());
          segBase = idParts.join('.');
          verbose && console.log(`segmentToColumns() override:`,
            JSON.stringify({articleId, segBase, segNum}));
        } else if (/<p/.test(line)){ 
          let colonParts = segBase.split(':');
          let idParts = colonParts[1].split('.');
          segNum = 1;
          let paraNum = Number(idParts.pop());
          idParts.push(paraNum+1);
          segBase = `${colonParts[0]}:${idParts.join('.')}`;
          verbose && console.log(`segmentToColumns() para:`,
            JSON.stringify({articleId, segBase, segNum}));
        }
        segment_id = `${segBase}.${segNum++}`;
        if (idMap[segment_id]) {
          segment_id = `${segment_id}.DUPLICATE${++idMap[segment_id]}`;
        } else {
          idMap[segment_id] = 1;
        }

        let root = (line.split('root>')[1] || '').replace(/<\/$/u,'');
        root = root || line
          .replace(/.*<segment[^>]*>/ug, '')
          .replace(/<\/segment>.*/ug, '');
        let commentParts = line.split('<comment>')
          .slice(1)
          .map(c=>c.replace(/<.comment>.*/iu, ''));
        let comment = commentParts.join('; ');

        yield { segment_id, html, root, comment, };
        html = '';
      }
    }

  }

    module.exports = exports.ParseHtml = ParseHtml;
})(typeof exports === "object" ? exports : (exports = {}));

