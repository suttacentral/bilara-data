(typeof describe === 'function') && describe("parse-html", function() {
    const should = require("should");
    const fs = require('fs');
    const path = require('path');
    const {
        ParseHtml,
    } = require("../index");

    let TEST_SF276_HTML = path.join(__dirname, 'data', 'sf276.html');
    let TEST_SF276_TSV = path.join(__dirname, 'data', 'sf276.tsv');

    it("default ctor", async()=>{
      let parser = new ParseHtml();
    });
    it("TESTTESThtmlSegments(fname)", async()=>{
      let verbose = 0;
      let parser = new ParseHtml();
      let htmlBuf = await fs.promises.readFile(TEST_SF276_HTML);
      let html = htmlBuf.toString().split('\n');
      let lines = [...await parser.htmlSegments(html, {verbose})];

      // each line has a segment
      for (let i=0; i<lines.length; i++) {
        let segments = lines[i].split(/<segment/);
        should(lines[i].split(/<segment/).length).equal(2, `lines[${i}]: ${lines[i]}`);
      }

      // first line has opening html
      should(lines[0]).match(/article.*<header.*h1.*<segment.*<\/header>$/);

      // last line has concluding html
      should(lines.slice(-1)[0]).match(/^<p><segment.*<.p><.article>$/);
    });
    it("TESTTESTsegmentsAsColumns(lines)", async()=>{
      let parser = new ParseHtml();
      let htmlBuf = await fs.promises.readFile(TEST_SF276_HTML);
      let html = htmlBuf.toString().split('\n');
      let segHtml = parser.htmlSegments(html);
      let segCols = [...parser.segmentsAsColumns(segHtml)];
      let parsedExpected = (await fs.promises.readFile(TEST_SF276_TSV))
        .toString()
        .split('\n')
        .map(line=>{
          let [ segment_id, html, root, comment ] = line.split('\t');
          return { segment_id, html, root, comment };
        });

      let i = -1;
      i++; should.deepEqual(segCols[i], parsedExpected[i+1]);
      i++; should.deepEqual(segCols[i], parsedExpected[i+1]);
      i++; should.deepEqual(segCols[i], parsedExpected[i+1]);
      i++; should.deepEqual(segCols[i], parsedExpected[i+1]);
      i++; should.deepEqual(segCols[i], parsedExpected[i+1]);
      i++; should.deepEqual(segCols[i], parsedExpected[i+1]);
      i++; should.deepEqual(segCols[i], parsedExpected[i+1]);
      i++; should.deepEqual(segCols[i], parsedExpected[i+1]);
    });

});

