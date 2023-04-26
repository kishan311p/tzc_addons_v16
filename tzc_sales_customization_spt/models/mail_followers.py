from odoo import _, api, fields, models, tools, Command

class mail_followers(models.Model):
    _inherit = 'mail.followers'

    def _add_followers(self, res_model, res_ids, partner_ids, subtypes,check_existing=False, existing_policy='skip'):
        _res_ids = res_ids or [0]
        data_fols, doc_pids = dict(), dict((i, set()) for i in _res_ids)

        if check_existing and res_ids:
            for fid, rid, pid, sids in self._get_subscription_data([(res_model, res_ids)], partner_ids or None):
                if existing_policy != 'force':
                    if pid:
                        doc_pids[rid].add(pid)
                data_fols[fid] = (rid, pid, sids)

            if existing_policy == 'force':
                self.sudo().browse(data_fols.keys()).unlink()

        new, update = dict(), dict()
        if not self._context.get('add_followers'):
            partner_ids = []
        for res_id in _res_ids:
            for partner_id in set(partner_ids or []):
                if partner_id not in doc_pids[res_id]:
                    new.setdefault(res_id, list()).append({
                        'res_model': res_model,
                        'partner_id': partner_id,
                        'subtype_ids': [Command.set(subtypes[partner_id])],
                    })
                elif existing_policy in ('replace', 'update'):
                    fol_id, sids = next(((key, val[2]) for key, val in data_fols.items() if val[0] == res_id and val[1] == partner_id), (False, []))
                    new_sids = set(subtypes[partner_id]) - set(sids)
                    old_sids = set(sids) - set(subtypes[partner_id])
                    update_cmd = []
                    if fol_id and new_sids:
                        update_cmd += [Command.link(sid) for sid in new_sids]
                    if fol_id and old_sids and existing_policy == 'replace':
                        update_cmd += [Command.unlink(sid) for sid in old_sids]
                    if update_cmd:
                        update[fol_id] = {'subtype_ids': update_cmd}

        return new, update