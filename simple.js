// import Nevow.Athena

if (typeof SimpleWidget == 'undefined') {
    SimpleWidget = {};
}

SimpleWidget.Button = Nevow.Athena.Widget.subclass();
SimpleWidget.Button.methods(
  function __init__(self, node) {
    SimpleWidget.Button.upcall(self, '__init__', node);
    self.callRemote('getLabel').addCallback(function (label) {
	input = node.getElementsByTagName("INPUT")[0];
	input.value = label;
    });
  },
  function click(self) {
      self.callRemote('onClick').addErrback(
        function (err) { Divmod.err(err); });
  });
