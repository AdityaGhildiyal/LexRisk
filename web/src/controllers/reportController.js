exports.showReport = (req, res) => {
  const { id } = req.params;
  const report = req.session.reports && req.session.reports[id];

  if (!report) {
    return res.redirect('/?error=Report not found or session expired');
  }

  res.render('report', { report, reportId: id });
};
